from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import streamlit as st;

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError
import sys

# .env file 참조
load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY')
AZURE_DEPLOYMENT_MODEL = "gpt-4.1-mini"  
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

try:
    search_credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)

    openai_client = AzureOpenAI(
        api_version="2024-06-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY
    )

    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name="risk-assessment-index",
        credential=search_credential
    )
    
except ClientAuthenticationError as e:
    print("API KEY를 확인해 주세요")
    sys.exit(1)
except HttpResponseError as e:
    print("엔드포인트를 확인해 주세요")
    sys.exit(1)
except Exception as e:
    print("알 수 없는 오류가 발생했습니다.")
    print(e)
    sys.exit(1)

# 프롬프트 생성
GROUNDED_PROMPT="""
You are a friendly assistant that recommends hotels based on activities and amenities.
Answer the query using only the sources provided below in a friendly and concise bulleted manner.
Answer ONLY with the facts listed in the list of sources below.
If there isn't enough information below, say you don't know.
Do not generate answers that don't use the sources below.
Query: {query}
Sources:\n{sources}
"""
# LLM 응답 함수 (AISEARCH + GPT 호출 포함)
def get_grounded_response(messages: list):
    user_query = messages[-1]['content']  # 마지막 유저 메시지 기준

    try:
        # Azure Search에서 검색
        search_result = search_client.search(
            search_text=user_query,
            top=5,
            select="Content,DocumentName,Tags"
        )
        search_results_list = list(search_result)
    except Exception as e:
        return f"검색 오류 발생: {e}"

    # 검색 결과가 없으면 LLM 호출
    if not search_results_list:
        response = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        llm_answer = response.choices[0].message.content
        if not st.session_state.shown_no_search_msg:
            st.session_state.shown_no_search_msg = True
            return "원하시는 답변을 찾지 못해, 제가 대답해드립니다: " + llm_answer
        else:
            return llm_answer

    sources_formatted = "\n".join([
        f'{doc["DocumentName"]}: {doc["Content"]}: {doc.get("Tags", [])}'
        for doc in search_results_list
    ])

    # GPT 입력 메시지
    messages = [
        {"role": "user",
         "content": GROUNDED_PROMPT.format(query=user_query, sources=sources_formatted)}
    ]

    # GPT 호출
    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT_MODEL,
        messages=messages,
        max_tokens=800,
        temperature=0.7,
    )

    return response.choices[0].message.content

# Streamlit UI 설정
st.title("위험성평가 Agent")
st.write("궁금한 것을 물어보세요")

# 채팅 기록의 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 안내 문구 표시 여부 플래그
if 'shown_no_search_msg' not in st.session_state:
    st.session_state.shown_no_search_msg = False

# 채팅 기록의 표시
for message in st.session_state.messages:
    st.chat_message(message['role']).write(message['content'])

if user_input :=st.chat_input("유해위험요인을 입력해주세요"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # LLM 응답 가져오기
    with st.spinner("응답을 기다리는 중..."):
        assistant_response = get_grounded_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.chat_message("assistant").write(assistant_response)