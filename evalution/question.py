import streamlit as st
from collections import defaultdict
from prompts.prompt import CHATBOT_QUESTION, CHATBOT_PROMPT, CHATBOT_EVALUATE
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
NUMBER_OF_QUESTION = 5

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

def evaluate_answers(model, question, expected_answer, received_answer):
    combined_prompt = CHATBOT_EVALUATE.format(
        question=question, expected_answer=expected_answer, received_answer=received_answer)
    response = model.generate_content(combined_prompt, safety_settings=safety_settings)
    return response.text.strip()


def get_embedding(text):
    # Tokenize the text into chunks of 256 tokens
    tokens = phobert_tokenizer.encode(text, truncation=False)
    chunks = [tokens[i:i + 256] for i in range(0, len(tokens), 256)]
    embeddings = []
    for chunk in chunks:
        input_ids = torch.tensor(chunk).unsqueeze(0).to(device)
        attention_mask = torch.ones(input_ids.size()).to(device)
        with torch.no_grad():
            output = phobert_model(input_ids, attention_mask=attention_mask)
        # Mean pooling
        embeddings_chunk = output.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(embeddings_chunk.size()).float()
        masked_embeddings = embeddings_chunk * mask
        summed_embeddings = torch.sum(masked_embeddings, 1)
        summed_mask = torch.clamp(mask.sum(1), min=1e-9)
        mean_pooled = summed_embeddings / summed_mask
        embeddings.append(mean_pooled.cpu().numpy())

    # Average embeddings from all chunks
    average_embedding = np.mean(embeddings, axis=0)
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
    st.write("Đang đánh giá chatbot...")
    st.write("Tiến trình truy xuất các bài báo và sinh câu hỏi:")
    progress_ask = st.progress(0)
    st.write("Tiến trình trả lời câu hỏi:")
    progress_answer = st.progress(0)
    st.write("Tiến trình đánh giá câu trả lời:")
    progress_eval = st.progress(0)

    # asking questions
    all_qa_data = ask_question(collection, model, NUMBER_OF_ARTICLE, progress_ask)
    # answering questions
    all_qa_data = answers(all_qa_data, model, collection, progress_answer)
    # evaluating the chatbot
    columns = ['title', 'url', 'question', 'expected_answer', 'received_answer', 
           'phobert_cossim', 'bert_cossim', 'roberta_nli', 'factbert_nli', 'chatbot_result']
    article_df = pd.DataFrame(columns=columns)
    len_of_answer = NUMBER_OF_ARTICLE * NUMBER_OF_QUESTION
    for art_idx, article in enumerate(all_qa_data):
        title = article['title']
        url = article['url']
        for q_idx, qa in enumerate(article['qa_pairs']):
            question = qa['question'][3:]
            expected_answer = qa['expected_answer'][3:]
            received_answer = qa['received_answer']
            
            phobert_results = cosine_score(expected_answer, received_answer)
            bertemb_results = util.cos_sim(bertemb_model.encode(expected_answer), bertemb_model.encode(received_answer))
            nli_roberta_results = nli_roberta_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            nli_factbert_results = nli_factbert_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            time.sleep(2)            
            chatbot_result = evaluate_answers(model, question, expected_answer, received_answer)            
            # Append the results directly to the DataFrame
            article_df = article_df.append({
                'title': title,
                'url': url,
                'question': question,
                'expected_answer': expected_answer,
                'received_answer': received_answer,
                'phobert_cossim': phobert_results[0][0],
                'bert_cossim': bertemb_results[0][0],
                'roberta_nli': nli_roberta_results[0]['label'],
                'factbert_nli': nli_factbert_results[0]['label'],
                'chatbot_result': chatbot_result
            }, ignore_index=True)
            progress_eval.progress((art_idx*NUMBER_OF_QUESTION + q_idx + 1) / len_of_answer)
   
    article_df.to_excel('evaluate.xlsx', index=False)
    sys.stdout = sys.__stdout__
    log_file.close()     
    
    # Display the summary table grouped by 'chatbot_result'
    total_rows = len(article_df)
    true_count = article_df[article_df['chatbot_result'] == "TRUE"].shape[0]
    true_percentage = (true_count / total_rows) * 100
    st.write(f"Phần trăm kết quả đúng theo 'chatbot_result': {true_percentage:.2f}%")
    category_count = article_df.groupby('chatbot_result').size().reset_index(name='count')
    summary_table = article_df.groupby('chatbot_result').agg({
        'phobert_cossim': 'mean',
        'bert_cossim': 'mean',
        'roberta_nli': lambda x: x.value_counts().to_dict(),
        'factbert_nli': lambda x: x.value_counts().to_dict(),
    }).reset_index()
    summary_table = pd.merge(category_count, summary_table, on='chatbot_result')
    st.write("Bảng tóm tắt kết quả theo 'chatbot_result'")
    st.dataframe(summary_table)
    return true_percentage
