import streamlit as st
from search.vector_search import preprocess_text

def get_conversation_history(max_tokens=1000):
    history = ""
    token_count = 0
    for message in reversed(st.session_state.messages[:-1]):  # Exclude the last message
        content = preprocess_text(message["content"])
        role = "Human: " if message["role"] == "user" else "Assistant: "
        message_text = f"{role}{content}\n"
        message_tokens = len(message_text.split())

        if token_count + message_tokens > max_tokens:
            break

        history = message_text + history
        token_count += message_tokens

    return history.strip()

def update_prompt_with_history(prompt_template, user_question, source_information):
    conversation_history = get_conversation_history()
    return prompt_template.format(
        conversation_history=conversation_history,
        user_question=preprocess_text(user_question),
        source_information=source_information
    )