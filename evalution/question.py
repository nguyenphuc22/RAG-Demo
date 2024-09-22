import streamlit as st
from collections import defaultdict
from prompts.prompt import CHATBOT_QUESTION, CHATBOT_PROMPT
from search.vector_search import get_search_result
from prompts.history import update_prompt_with_history
from transformers import AutoModel, AutoTokenizer, pipeline
import torch
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Union
import numpy as np
import time
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from sentence_transformers import SentenceTransformer, util
import re
import pandas as pd
import sys


###### CONFIGURATION ######
NUMBER_OF_ARTICLE = 20
NUMBER_OF_QUESTION = 10

phobert_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
phobert_model = AutoModel.from_pretrained("vinai/phobert-base")
bertemb_model = SentenceTransformer('bert-base-nli-mean-tokens')
nli_roberta_model = pipeline("text-classification", model="joeddav/xlm-roberta-large-xnli")
nli_factbert_model = pipeline("text-classification", model="facebook/bart-large-mnli")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("CUDA ", device)
phobert_model.to(device)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, }

###### FUNCTIONS ######

def extract_qa_pairs(text):
    qa_pairs = re.findall(r'(Q: .*?)(A: .*?)(?=Q:|$)', text, re.DOTALL)    
    return [{"question": q.strip(), "expected_answer": a.strip()} for q, a in qa_pairs]

def answers(all_qa_data, model, collection, progress_answer):
    len_of_answer = NUMBER_OF_ARTICLE * NUMBER_OF_QUESTION
    for art_idx, article in enumerate(all_qa_data):
        for q_idx, qa in enumerate(article['qa_pairs']):
            time.sleep(2)   #wait for resource availability
            question = qa['question'][3:]
            print("\tQuestion: ", question)
            source_information = get_search_result(question.lower(), collection)
            combined_prompt = CHATBOT_PROMPT.format(
                conversation_history="", user_question=question, source_information=source_information)
            response = model.generate_content(
                combined_prompt, safety_settings=safety_settings)   
            qa['received_answer'] = response.text
            progress_answer.progress((art_idx*NUMBER_OF_QUESTION + q_idx + 1) / len_of_answer)
    return all_qa_data

def ask_question(collection, model, number_of_article, progress_ask):
    all_question = []
    articles = defaultdict(list)
    complete_articles = []

    projection = {'embedding': 0}
    documents = collection.find({}, projection)
    for chunk in documents:
        articles[chunk['url']].append(chunk)
    for id, item in articles.items():
        sorted_chunks = sorted(item, key=lambda x: x['chunk_index'])
        full_content = ''.join(chunk['chunk_content']
                               for chunk in sorted_chunks)
        title = sorted_chunks[0]['title']
        url = sorted_chunks[0]['url']
        complete_article = {'title': title, 'url': url, 'content': full_content}
        complete_articles.append(complete_article)
    for id, article in enumerate(complete_articles[:number_of_article]):
        time.sleep(2)
        print("Article title: ", article['title'])
        question = model.generate_content(CHATBOT_QUESTION.format(
            information=article['content'], number_of_question=NUMBER_OF_QUESTION), safety_settings=safety_settings)        
        qa_pairs = extract_qa_pairs(question.text)
        article_qa_data = {
            'title': article['title'],
            'url': article['url'],
            'qa_pairs': qa_pairs
        }
        all_question.append(article_qa_data)
        progress_ask.progress((id+1)/(number_of_article))
    return all_question


def get_embedding(text, max_length=256):
    inputs = phobert_tokenizer(text, return_tensors='pt',
                       padding=True, truncation=True, max_length=max_length)
    input_ids = inputs['input_ids'].to(device)
    embeddings = []
    if input_ids.size(1) <= 256:
        split_input_ids = [input_ids]
    else:
        split_input_ids = torch.split(input_ids, 256, dim=1)
    for split_token in split_input_ids:
        with torch.no_grad():
            output = phobert_model(split_token)
        embeddings.append(output.last_hidden_state[:, 0, :].cpu().numpy())
    average_embedding = sum(embeddings) / len(embeddings)
    return average_embedding


def cosine_score(answer, info):
    embedding1 = get_embedding(answer)
    embedding2 = get_embedding(info)
    return cosine_similarity(embedding1, embedding2)


def evaluation(collection, model):
    # Open a log file
    log_file = open('output.log', 'w', encoding='utf-8')
    sys.stdout = log_file 
    st.session_state.messages = []
    st.write("Evaluating the chatbot...")
    st.write("Progress of retrieving articles and generating questions:")
    progress_ask = st.progress(0)
    st.write("Progress of answering questions:")
    progress_answer = st.progress(0)
    st.write("Progress of evaluating the chatbot:")
    progress_eval = st.progress(0)

    # asking questions
    all_qa_data = ask_question(collection, model, NUMBER_OF_ARTICLE, progress_ask)
    # answering questions
    all_qa_data = answers(all_qa_data, model, collection, progress_answer)
    # evaluating the chatbot
    len_of_answer = NUMBER_OF_ARTICLE * NUMBER_OF_QUESTION
    for art_idx, article in enumerate(all_qa_data):
        for q_idx, qa in enumerate(article['qa_pairs']):
            expected_answer = qa['expected_answer'][3:]
            received_answer = qa['received_answer']
            phobert_results = cosine_score(expected_answer, received_answer)
            bertemb_results = util.cos_sim(bertemb_model.encode(expected_answer), bertemb_model.encode(received_answer))
            nli_roberta_results = nli_roberta_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            nli_factbert_results = nli_factbert_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            qa['cossim1_phobert'] = phobert_results
            qa['cossim2_bert'] = bertemb_results
            qa['nli1_roberta'] = nli_roberta_results
            qa['nli2_factbert'] = nli_factbert_results
            progress_eval.progress((art_idx*NUMBER_OF_QUESTION + q_idx + 1) / len_of_answer)
                    
    # saving to excel  
    data = []  
    for article_dict in all_qa_data:
        title = article_dict['title']
        url = article_dict['url']             
        for qa in article_dict['qa_pairs']:
            question = qa['question'][3:]
            expected_answer = qa['expected_answer'][3:]
            received_answer = qa['received_answer']
            cossim1_phobert = qa['cossim1_phobert']
            cossim2_bert = qa['cossim2_bert']
            nli1_roberta = qa['nli1_roberta']
            nli2_factbert = qa['nli2_factbert']
            data.append([title, url, question, expected_answer, received_answer, cossim1_phobert, cossim2_bert, nli1_roberta, nli2_factbert])                
    article_df = pd.DataFrame(data, columns=['title', 'url', 'question', 'expected_answer', 'received_answer', 'phobert_cossim', 'bert_cossim', 'roberta_nli', 'factbert_nli'])
    article_df.to_excel('evaluate.xlsx', index=False)
    average_score = article_df['bert_cossim'].mean()
    sys.stdout = sys.__stdout__
    log_file.close()     
    return average_score
