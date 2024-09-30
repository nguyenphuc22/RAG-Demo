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
phobert_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
phobert_model = AutoModel.from_pretrained("vinai/phobert-base")
bertemb_model = SentenceTransformer('bert-base-nli-mean-tokens')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("CUDA ", device)
nli_roberta_model = pipeline("text-classification", model="joeddav/xlm-roberta-large-xnli", device=device)
nli_factbert_model = pipeline("text-classification", model="facebook/bart-large-mnli", device=device)
# phobert_model.to(device)
# bertemb_model.to(device)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, }

###### FUNCTIONS ######

def extract_qa_pairs(text):
    qa_pairs = re.findall(r'(Q: .*?)(A: .*?)(?=Q:|$)', text, re.DOTALL)    
    return [{"question": q.strip(), "expected_answer": a.strip()} for q, a in qa_pairs]

def answers(eval_df, model, collection, progress_answer):
    len_of_answer = len(eval_df)    
    for idx, row in eval_df.iterrows():
        time.sleep(2)   #wait for resource availability
        question = row['question']
        print("\tQuestion: ", question)
        source_information = get_search_result(question.lower(), collection)
        combined_prompt = CHATBOT_PROMPT.format(
            conversation_history="", user_question=question, source_information=source_information)
        response = model.generate_content(
            combined_prompt, safety_settings=safety_settings)
        eval_df.at[idx, 'received_answer'] = response.text
        progress_answer.progress((idx+1) / len_of_answer)
    return eval_df

def ask_question(collection, model, number_of_article, number_of_question, progress_ask):
    articles = defaultdict(list)
    complete_articles = []
    eval_df = pd.DataFrame(columns=['title', 'url', 'question', 'expected_answer'])

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
            information=article['content'], number_of_question=number_of_question), safety_settings=safety_settings)        
        qa_pairs = extract_qa_pairs(question.text)
        for qa in qa_pairs:
            article_qa_data = {
                'title': article['title'],
                'url': article['url'],
                'question': qa['question'],
                'expected_answer': qa['expected_answer']
            }
            if eval_df.empty:
                eval_df = pd.DataFrame(article_qa_data, index=[0])
            else:
                eval_df.loc[len(eval_df)] = article_qa_data
        progress_ask.progress((id+1)/(number_of_article))
    return eval_df

def evaluate_answers(model, question, expected_answer, received_answer):
    combined_prompt = CHATBOT_EVALUATE.format(
        question=question, expected_answer=expected_answer, received_answer=received_answer)
    response = model.generate_content(combined_prompt, safety_settings=safety_settings)
    return response.text.strip()


def get_embedding(text):
    inputs = phobert_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = phobert_model(**inputs)
    return outputs.last_hidden_state[:, 0, :]  # CLS token embedding



def cosine_score(answer, info):
    embedding1 = get_embedding(answer).cpu().numpy()
    embedding2 = get_embedding(info).cpu().numpy()
    return cosine_similarity(embedding1, embedding2)


def evaluation(collection, model):
    st.title("Đánh giá chatbot 🔎")    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Lựa chọn số lượng testcases:")
        st.session_state.no_articles = st.number_input("Số lượng bài báo cần kiểm thử: ", value=st.session_state.get("no_articles", 20))
        st.session_state.no_question = st.number_input("Số lượng câu hỏi cho mỗi bài báo: ", value=st.session_state.get("no_question", 5))
    with col2:
        st.subheader("So sánh với các mô hình tính toán độ tương đồng ngữ nghĩa:")
        st.session_state.phobert_opt = st.checkbox("PhoBERT", value=st.session_state.get("phobert_opt", True))
        st.session_state.bertemb_opt = st.checkbox("BERT-Base", value=st.session_state.get("bertemb_opt", True))
    with col3:
        st.subheader("So sánh với các mô hình suy luận ngôn ngữ tự nhiên (NLI):")
        st.session_state.roberta_opt = st.checkbox("XLM-RoBERTa", value=st.session_state.get("roberta_opt", True))
        st.session_state.factbert_opt = st.checkbox("BART-Large-MNLI", value=st.session_state.get("factbert_opt", True))

    result = 0
    if st.button("Bắt đầu kiểm thử"):
        result = _evaluation(collection, model,
                                              st.session_state.no_articles, st.session_state.no_question,
                                              st.session_state.phobert_opt, st.session_state.bertemb_opt, 
                                              st.session_state.roberta_opt, st.session_state.factbert_opt)

    return result

def _evaluation(collection, model, no_articles, no_question, phobert_opt, bertemb_opt, roberta_opt, factbert_opt):
    # Open a log file
    log_file = open('output.log', 'w', encoding='utf-8')
    sys.stdout = log_file 
    st.subheader("Đang đánh giá chatbot...")
    st.write("Tiến trình truy xuất các bài báo và sinh câu hỏi:")
    progress_ask = st.progress(0)
    st.write("Tiến trình trả lời câu hỏi:")
    progress_answer = st.progress(0)
    st.write("Tiến trình đánh giá câu trả lời:")
    progress_eval = st.progress(0)

    # asking questions
    eval_df = ask_question(collection, model, no_articles, no_question, progress_ask)
    # answering questions
    eval_df = answers(eval_df, model, collection, progress_answer)
    # evaluating the chatbot
    len_of_answer = len(eval_df)
    for idx, row in eval_df.iterrows():
        question = row['question']
        expected_answer = row['expected_answer']
        received_answer = row['received_answer']
        if phobert_opt:
            phobert_results = cosine_score(expected_answer, received_answer)
            eval_df.at[idx, 'phobert_cossim'] = phobert_results[0][0]
        if bertemb_opt:
            bertemb_results = util.cos_sim(bertemb_model.encode(expected_answer), bertemb_model.encode(received_answer))
            eval_df.at[idx, 'bert_cossim'] = bertemb_results.item()
        if roberta_opt:
            nli_roberta_results = nli_roberta_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            eval_df.at[idx, 'roberta_nli'] = nli_roberta_results[0]['label']
        if factbert_opt:
            nli_factbert_results = nli_factbert_model(f"premise: {expected_answer} hypothesis: {received_answer}")
            eval_df.at[idx, 'factbert_nli'] = nli_factbert_results[0]['label']
        time.sleep(2)
        chatbot_result = evaluate_answers(model, question, expected_answer, received_answer)
        eval_df.at[idx, 'chatbot_result'] = chatbot_result
        progress_eval.progress((idx+1) / len_of_answer)

   
    sys.stdout = sys.__stdout__
    log_file.close()     
    eval_df.to_excel('evaluate.xlsx', index=False)
    
    # Display the summary table grouped by 'chatbot_result'
    st.subheader("Kết quả đánh giá chatbot:")
    total_rows = len(eval_df)
    true_count = eval_df[eval_df['chatbot_result'] == "TRUE"].shape[0]
    true_percentage = (true_count / total_rows) * 100
    st.write(f"Phần trăm kết quả đúng theo do LLM đánh giá: {true_percentage:.2f}%")
    if phobert_opt:
        st.write(f"Đánh giá độ tương đồng ngữ nghĩa trung bình sử dụng PhoBERT: {eval_df['phobert_cossim'].mean()}")
    if bertemb_opt:
        st.write(f"Đánh giá độ tương đồng ngữ nghĩa trung bình sử dụng BERT-Base: {eval_df['bert_cossim'].mean()}")
    if roberta_opt:
        st.write(f"Đánh giá suy luận ngôn ngữ sử dụng XLM-RoBERTa: {eval_df['roberta_nli'].value_counts().to_dict()}")
    if factbert_opt:
        st.write(f"Đánh giá suy luận ngôn ngữ sử dụng BART-Large-MNLI: {eval_df['factbert_nli'].value_counts().to_dict()}")

    group_columns = ['chatbot_result']
    available_mean_columns = [col for col in ['phobert_cossim', 'bert_cossim'] if col in eval_df.columns]
    available_nli_columns = [col for col in ['roberta_nli', 'factbert_nli'] if col in eval_df.columns]
    agg_dict = {}
    for col in available_mean_columns:
        agg_dict[col] = 'mean'
    for col in available_nli_columns:
        agg_dict[col] = lambda x: x.value_counts().to_dict()
    if agg_dict:
        category_count = eval_df.groupby(group_columns).size().reset_index(name='count')
        summary_table = eval_df.groupby(group_columns).agg(agg_dict).reset_index()
        summary_table = pd.merge(category_count, summary_table, on='chatbot_result')
        st.write(summary_table)
    return true_percentage
