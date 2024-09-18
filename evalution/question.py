import streamlit as st
from collections import defaultdict
from prompts.prompt import CHATBOT_QUESTION, CHATBOT_PROMPT
from search.vector_search import get_search_result
from prompts.history import update_prompt_with_history
from transformers import AutoModel, AutoTokenizer
import torch
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Union
import numpy as np
import time
from google.generativeai.types import HarmCategory, HarmBlockThreshold


tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("CUDA ", device)
model.to(device)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, }


def answers(prompt, model, collection) -> Dict[str, Union[str, List[str]]]:
    time.sleep(2)
    source_information = get_search_result(prompt.lower(), collection)
    combined_prompt = update_prompt_with_history(
        CHATBOT_PROMPT, prompt, source_information)
    response = model.generate_content(
        combined_prompt, safety_settings=safety_settings)

    response_text = response.text
    print("-----------Answer CHATBOT:", response_text)
    lines = source_information.split('\n')
    info = []
    for line in lines:
        if line.strip().startswith('Trích đoạn:'):
            excerpt = line.replace('Trích đoạn:', '').strip()
            info.append(excerpt)
    return {"text": response.text, "info": info}


def ask_question(collection, model):
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
        complete_article = {'title': title, 'content': full_content}
        complete_articles.append(complete_article)
    for article in complete_articles[:5]:
        time.sleep(2)
        question = model.generate_content(CHATBOT_QUESTION.format(
            information=article['content'], title=article['title']), safety_settings=safety_settings)
        split_questions = [item.strip()
                           for item in question.text.split('?') if item.strip()]
        questions = [item + '?' for item in split_questions]
        for i, question in enumerate(questions):
            print(f"{i+1}. {question}")
            all_question.append(question)
    return all_question


def get_embedding(text, max_length=256):
    inputs = tokenizer(text, return_tensors='pt',
                       padding=True, truncation=True, max_length=max_length)
    input_ids = inputs['input_ids'].to(device)
    embeddings = []
    if input_ids.size(1) <= 256:
        split_input_ids = [input_ids]
    else:
        split_input_ids = torch.split(input_ids, 256, dim=1)
    for split_token in split_input_ids:
        with torch.no_grad():
            output = model(split_token)
        embeddings.append(output.last_hidden_state[:, 0, :].cpu().numpy())
    average_embedding = sum(embeddings) / len(embeddings)
    return average_embedding


def cosine_score(answer, info):
    embedding1 = get_embedding(answer)
    embedding2 = get_embedding(info)
    return cosine_similarity(embedding1, embedding2)


def evaluation(collection, model):
    st.session_state.messages = []
    with st.spinner('Evaluation...'):
        list_question = ask_question(collection, model)
        list_answer = []
        total_score = []
        for question in list_question:
            result_answer = answers(question, model, collection)
            if result_answer['text'] == "":
                continue
            else:
                list_answer.append(result_answer)
        for answer in list_answer:
            local_score = []
            for info in answer['info']:
                local_score.append(cosine_score(answer['text'], info))
            print("-----local score ", local_score)
            total_score.append(np.max([array for array in local_score]))
        return np.mean([item for item in total_score])
