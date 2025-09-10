import openai
from dotenv import load_dotenv
import os
import streamlit as st;

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.azure_endpoint = os.getenv('AZURE_ENDPOINT')
openai.api_type = os.getenv('OPENAI_API_TYPE')
openai.api_version = os.getenv('OPENAI_API_VERSION')

def get_LLM_response(messages):
    response = openai.chat.completions.create(
        model="dev-gpt-4.1-mini",  
        messages=messages,
        max_tokens= 1000,
        temperature= 0.7,
    )
    return response.choices[0].message.content


# 스트림잇 앱 설정
st.title("Azure OpenA Chatbot")
st.write("궁금한 것을 물어보세요")

# 채팅 기록의 초기화
if 'message' not in st.session_state:
    st.session_state.messages = []

# 채팅 기록의 표시
for messages in st.session_state.messages:
    st.chat_message(message['role']).write(message['content'])

if user_input :=st.chat_input("메세지를 입력하세요"):

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # LLM 응답 가져오기
    with st.spinner("응답을 기다리는 중..."):
        assistant_response = get_LLM_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.chat_message("assistant").write(assistant_response)