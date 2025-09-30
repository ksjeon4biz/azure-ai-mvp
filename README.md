# azure-ai-mvp

✅ 목표 요약

입력: 매일 생성되는 서버 로그 파일 (.log, .txt, .json 등)

처리: Azure Function이 로그 업로드 감지 → 특정 정규식 탐지 → RAG 벡터화

검색: RAG 기반 챗봇이 Streamlit에서 로그 기반 질의 응답 제공

보안: 내부 데이터로만 학습, 외부 유출 없음

📅 3일 개발 계획 (Day-by-Day)
📌 Day 1 – 프로젝트 구조 + Azure 리소스 + 기본 파이프라인

목표: 전체 흐름 구성과 Azure 리소스 준비

1.1. 프로젝트 구조 설계
logbot_project/
├── backend/
│   ├── azure_function/       # 로그 업로드 트리거 및 정규식 처리
│   ├── rag_pipeline/         # 임베딩 + 벡터DB 저장
│   └── langchain/            # QA 체인 구성
├── frontend/
│   └── streamlit_app/        # 질의 응답 UI
├── data/
│   └── logs/                 # 로그 보관
├── configs/
│   └── regex_patterns.json   # 탐지 정규식
└── .env

1.2. Azure 리소스 생성 (Azure Portal or CLI)

✅ Azure Storage Blob (log 업로드용)

✅ Azure Function App (Blob Trigger 방식)

✅ Azure AI Search (벡터 검색용)

✅ Azure AI Services (임베딩 / 언어분석)

✅ Azure Language or OpenAI (GPT-4.1-mini API Key)

1.3. Azure Function 준비

트리거: Blob container log-upload/에 파일이 업로드되면 실행

기능: 로그에서 지정한 정규식(예: ERROR, Exception) 탐지

결과: 탐지 내용과 함께 벡터화 요청 (→ rag_pipeline)

☑️ Output 예시 JSON:

{
  "filename": "server_20250927.log",
  "matches": ["NullPointerException at line 293", "Connection timeout"],
  "summary": "2 errors detected",
  "upload_time": "2025-09-27T00:03:21"
}

📌 Day 2 – RAG 구성 (LangChain 기반) + 벡터 저장
2.1. RAG 구성 요소

Document Loader: 로그 파일의 라인별 entry 나누기

Text Splitter: LangChain의 CharacterTextSplitter 사용

Embedding Model: AzureOpenAIEmbeddings or OpenAIEmbeddings

Vector Store: Azure Cognitive Search

Retriever: SearchRetriever() + filter 조건 (파일명, 날짜 등)

2.2. LangChain QA Chain 구성

ConversationalRetrievalChain 사용

시스템 프롬프트: "서버 로그를 기반으로 정확한 문제 설명과 원인을 요약해주세요."

Memory: LangGraph로 간단한 세션 흐름 구성 가능 (옵션)

2.3. LangSmith / LangFuse 연동

LangSmith: QA 체인 추적 및 debug

LangFuse: 응답 품질 모니터링 및 에러 추적

📌 Day 3 – Streamlit 챗봇 UI + 통합 테스트 + 마무리
3.1. Streamlit 챗봇 UI

입력창: 사용자 질문

옵션:

날짜 선택 (→ 해당 로그파일만 검색)

에러 타입 필터 (예: Timeout, NullPointer, 사용자 정의)

출력: 응답 + 관련 로그 하이라이트

st.title("🪵 로그 분석 챗봇")
query = st.text_input("무엇이 궁금한가요?")
if query:
    answer = qa_chain.run({"question": query})
    st.write(answer)

3.2. 통합 흐름 테스트

로그 파일 업로드 → Function 트리거 → 정규식 탐지 및 임베딩

검색 가능한 벡터 저장 확인

Streamlit에서 질의 → 로그 기반 응답 확인

3.3. 문서화 및 README 정리

실행 방법, 환경변수 설정, 리소스 의존성 명시

⚙️ 기술 스택 요약
목적	기술
업로드 감지	Azure Function (Blob Trigger)
문서 전처리	LangChain Loader + Splitter
벡터 임베딩	Azure OpenAI Embedding
검색 백엔드	Azure AI Search
QA 체인	LangChain ConversationalRetrievalChain
프론트엔드	Streamlit
분석 추적	LangSmith, LangFuse
🔐 보안 고려사항

로그파일은 절대 외부 전송 금지

Azure Function + Storage + Search는 같은 리소스 그룹 내부

.env 사용하여 키, 정규식 경로 등 보관

🔄 선택적으로 고려할 확장

LangGraph로 상태 흐름 구성 (예: 파일 업로드 → 처리 중 → 완료)

LLM 응답을 기반으로 추론된 문제 요약 자동 생성

PDF로 리포트 저장 or 이메일 전송

이제 이 계획에 대한 의견이나 수정하고 싶은 부분을 말씀해 주세요!
(예: 로그파일 포맷, 정규식 구체화, LangGraph 비중 확대, 챗봇 UI 추가기능 등)




1일차 ============================================================================

좋습니다. 이제부터 저는 Azure 기반 RAG + LangChain + 로그 분석 파이프라인 전문가의 입장에서,
1일차 작업을 순서별로 세분화해서 **"복붙해서 바로 쓸 수 있는 수준"**으로 드릴게요.
당신이 3일 안에 완성할 수 있도록 초보자 난이도, 현업 실용성, 빠른 반복 검증을 고려했습니다.

📅 1일차 상세 작업 순서

목표: Azure 리소스 생성 + 로그 트리거 파이프라인 기본 구성 + 프로젝트 디렉토리 정리

✅ 1.1. 프로젝트 디렉토리 생성 (로컬 개발 환경 기준)
mkdir logbot_project && cd logbot_project

# 기본 구조 생성
mkdir -p backend/azure_function
mkdir -p backend/rag_pipeline
mkdir -p backend/langchain
mkdir -p frontend/streamlit_app
mkdir -p data/logs
mkdir -p configs

touch .env


참고: .env는 API 키, connection string, 정규식 경로 등을 저장할 용도

✅ 1.2. Azure 리소스 그룹 및 리소스 생성

💡 CLI 또는 Azure Portal 중 선택 가능하지만, Azure CLI로 명령어 드릴게요.

# 환경 변수 정의 (복사 후 값만 수정)
RESOURCE_GROUP=logbot-rg
LOCATION=eastus
STORAGE_ACCOUNT=logbotstorage$RANDOM
FUNCTION_APP=logbot-function$RANDOM
SEARCH_SERVICE=logbot-search
COGNITIVE_SERVICE=logbot-ai

# 1. 리소스 그룹 생성
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Storage 계정 생성
az storage account create \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --sku Standard_LRS

# 3. Function App을 위한 App Service Plan 생성
az functionapp plan create \
  --resource-group $RESOURCE_GROUP \
  --name logbot-plan \
  --location $LOCATION \
  --number-of-workers 1 \
  --sku B1 \
  --is-linux

# 4. Function App 생성 (Python 런타임)
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --plan logbot-plan \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4

# 5. Azure AI Search 생성
az search service create \
  --name $SEARCH_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku basic

# 6. Azure AI 서비스 생성 (임베딩용)
az cognitiveservices account create \
  --name $COGNITIVE_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --kind CognitiveServices \
  --sku S0 \
  --location $LOCATION \
  --yes


생성 완료 후 필요한 키들을 .env에 저장해 두세요
(Function Key, Cognitive Services Key, Search Admin Key 등)

✅ 1.3. Azure Blob Storage 컨테이너 생성 및 업로드 테스트
# Storage Connection String 확인
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv

# 로컬에서 test 컨테이너 만들고 로그파일 업로드
az storage container create \
  --name log-upload \
  --account-name $STORAGE_ACCOUNT \
  --public-access off

az storage blob upload \
  --container-name log-upload \
  --file ./data/logs/sample_log.txt \
  --name 2025-09-27.log \
  --account-name $STORAGE_ACCOUNT

✅ 1.4. Azure Function 로컬 개발 및 배포 준비
cd backend/azure_function
func init log_uploader --python
cd log_uploader
func new --name LogTrigger --template "Azure Blob Storage trigger" --authlevel "function"


🔧 생성된 LogTrigger/__init__.py를 아래와 같이 편집하세요:

import logging
import re
import os
import json

import azure.functions as func

PATTERN_LIST = [
    r"Exception",
    r"Timeout",
    r"Connection refused",
    r"NullPointerException",
]

def main(myblob: func.InputStream):
    logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

    content = myblob.read().decode("utf-8")
    matches = []
    for pattern in PATTERN_LIST:
        matches += re.findall(pattern, content)

    summary = {
        "filename": myblob.name,
        "match_count": len(matches),
        "matched_patterns": matches,
    }

    logging.info(f"Match Summary: {json.dumps(summary, indent=2)}")


🔧 function.json 설정 확인 (path, connection 등):

{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "name": "myblob",
      "type": "blobTrigger",
      "direction": "in",
      "path": "log-upload/{name}",
      "connection": "AzureWebJobsStorage"
    }
  ]
}

✅ 1.5. Function 로컬 실행 테스트
# 가상환경 및 의존 설치
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 로컬 실행
func start

✅ 1.6. 기능 확인 체크리스트

 로그파일 업로드 시 Function 트리거 작동 확인

 정규식 패턴 탐지 로그 출력 확인

 sample_log.txt 안에 일부러 "NullPointerException" 같은 문자열 포함해 테스트

 정규식은 configs/regex_patterns.json 으로 추후 분리 가능

✅ 1.7. TODO로 남길 것 (Day 2로 넘김)

 탐지된 로그 → Azure Search에 저장할 수 있도록 후속처리

 LangChain에서 벡터검색 가능하도록 구성

 LangSmith / LangFuse 연동

 Streamlit 챗봇 연결

✅ 1일차 결과물

Azure 리소스 구성 완료

로그 업로드 → 정규식 탐지 → Function 로그 출력까지 확인

프로젝트 폴더 및 개발환경 세팅 완료

📌 다음 단계 제안

1일차 진행 후, 로그 파일 포맷을 공유해 주시면
👉 LangChain TextLoader + Splitter + Document 준비까지 이어서 설계해 드리겠습니다.





2일차 ======================================================================================

좋아요 👍
이제 2일차는 RAG 파이프라인 + Azure AI Search 연결이 핵심입니다.
목표는 정규식으로 탐지한 로그 내용을 Azure Cognitive Search(벡터 DB)에 넣고, LangChain으로 검색 + 질문응답이 가능하게 만드는 것입니다.

아래 단계는 실무형이면서도 3일 안에 완성 가능한 난이도로 설계했습니다.

📅 2일차 상세 계획

목표: RAG 파이프라인 구성 + Azure Search 인덱스 생성 + LangChain으로 질의응답 가능 상태 만들기

✅ 2.1. Python 환경 준비 (벡터화/인덱싱 스크립트용)
cd backend/rag_pipeline
python -m venv .venv
source .venv/bin/activate    # (Windows: .venv\Scripts\activate)

pip install langchain-openai azure-search-documents azure-identity python-dotenv


⚡ 추가 패키지:

langchain-openai : OpenAI 임베딩 & Chat 모델

azure-search-documents : Azure Cognitive Search SDK

azure-identity : Azure 자격 증명

python-dotenv : .env 로부터 키 로딩

✅ 2.2. .env 파일 갱신
# .env
AZURE_SEARCH_ENDPOINT=https://<SEARCH_SERVICE>.search.windows.net
AZURE_SEARCH_KEY=<관리자키>
AZURE_OPENAI_API_KEY=<OpenAI Key>
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SEARCH_INDEX_NAME=log-index


💡 AZURE_SEARCH_KEY 는 Azure Portal → AI Search → Keys & Endpoint → Admin Key 복사
💡 OpenAI 대신 Azure OpenAI를 쓰려면 AZURE_OPENAI_ENDPOINT 와 AZURE_OPENAI_API_VERSION도 추가

✅ 2.3. Azure Cognitive Search 인덱스 생성 스크립트

create_search_index.py 작성:

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType, SearchableField, VectorSearch,
    VectorSearchAlgorithmConfiguration, HnswAlgorithmConfiguration, VectorSearchProfile,
    SearchField
)
from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.environ["SEARCH_INDEX_NAME"]

index_client = SearchIndexClient(endpoint, AzureKeyCredential(key))

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="filename", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="timestamp", type=SearchFieldDataType.String, filterable=True),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile="default"
    )
]

vector_search = VectorSearch(
    algorithm_configurations=[
        HnswAlgorithmConfiguration(name="default", kind="hnsw")
    ],
    profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="default")]
)

index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)

# 기존 인덱스 삭제 후 재생성(개발용)
try:
    index_client.delete_index(index_name)
    print(f"Deleted existing index {index_name}")
except:
    pass

index_client.create_index(index)
print(f"Index {index_name} created!")


⚡ 실행:

python create_search_index.py

✅ 2.4. 벡터화 & 문서 업로드 스크립트

upload_docs.py 작성:

import os, uuid, datetime
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.environ["SEARCH_INDEX_NAME"]

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))
embeddings = OpenAIEmbeddings(model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"), api_key=os.getenv("AZURE_OPENAI_API_KEY"))

def upload_log(filename, content):
    # 임베딩 생성
    vector = embeddings.embed_documents([content])[0]

    doc = {
        "id": str(uuid.uuid4()),
        "content": content,
        "filename": filename,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "content_vector": vector
    }

    search_client.upload_documents([doc])
    print(f"Uploaded: {filename}")

if __name__ == "__main__":
    # 샘플 테스트
    with open("../azure_function/log_uploader/sample_log.txt", "r", encoding="utf-8") as f:
        text = f.read()
    upload_log("sample_log.txt", text)


⚡ 실행:

python upload_docs.py


→ Cognitive Search 포털에서 인덱스 안에 문서가 올라갔는지 확인.

✅ 2.5. Azure Function과 연동 (자동 업로드)

Day1에서 만든 function_app.py 안에, 정규식 탐지 후 벡터 업로드 호출 추가:

import logging
import azure.functions as func
import re, json, os, uuid, datetime
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import OpenAI

app = func.FunctionApp()

# Azure Search 클라이언트
search_client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["SEARCH_INDEX_NAME"],
    credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
)

# OpenAI 임베딩
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"), api_key=os.getenv("AZURE_OPENAI_API_KEY"))

@app.function_name(name="LogTrigger")
@app.blob_trigger(arg_name="myblob", path="log-upload/{name}", connection="AzureWebJobsStorage")
def log_trigger(myblob: func.InputStream):
    logging.info(f"Processing blob: {myblob.name}")
    content = myblob.read().decode("utf-8")

    # 정규식 탐지
    patterns = [r"Exception", r"Timeout", r"Connection refused"]
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, content))
    logging.info(f"Match Summary: {matches}")

    # 벡터 생성 후 업로드
    vector = embeddings.embed_documents([content])[0]
    doc = {
        "id": str(uuid.uuid4()),
        "content": content,
        "filename": myblob.name,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "content_vector": vector
    }
    search_client.upload_documents([doc])
    logging.info("Uploaded to Azure Search")


⚡ 로컬에서 다시 func start 후 Blob 업로드 테스트 → Cognitive Search 인덱스에 자동 등록되는지 확인

✅ 2.6. LangChain Retriever + QA Chain 테스트

test_qa.py 작성:

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores.azuresearch import AzureSearch

load_dotenv()

vectorstore = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("SEARCH_INDEX_NAME"),
    embedding_function=None,  # 이미 인덱스에 벡터 있음
)

retriever = vectorstore.as_retriever(search_type="similarity", k=3)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

qa = RetrievalQA.from_chain_type(llm, retriever=retriever)

query = "최근 업로드된 로그에서 Exception이 발생한 부분을 요약해줘"
print(qa.run(query))


⚡ 실행:

python test_qa.py

✅ 2.7. LangSmith / LangFuse 연동 (선택)

LangSmith: LLM 응답 추적용

pip install langsmith
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your_langsmith_key>


LangFuse: 품질/로그 모니터링용

pip install langfuse


개발 단계에서는 꼭 필수는 아니지만, 챗봇 품질을 분석하고 싶으면 설정해두면 좋습니다.

✅ 2일차 완료 체크리스트

 Azure Cognitive Search 인덱스 생성 성공

 Function이 Blob 업로드 → 정규식 탐지 → 벡터 업로드 자동화

 test_qa.py 로 LangChain QA 체인 질의응답 확인

 (옵션) LangSmith/LangFuse 추적 활성화

🔥 3일차 미리보기

Streamlit 챗봇 UI 구축 (사용자 입력 → LangChain QA → 결과 출력)

날짜 필터 / 로그 파일명 필터 기능 추가

운영 환경에서 Function App 배포 및 엔드투엔드 테스트

이제 2일차 단계 중에서

로그 포맷 세부 처리 방법

정규식 관리 (JSON 파일로 분리)

Azure OpenAI vs OpenAI API 차이 설정
같은 부분이 궁금하다면 추가로 알려드릴까요?
또는 바로 2일차 작업부터 실행해 보시겠어요?



3일차 ======================================================================

좋아요! 이제 3일차에서 할 일들을 “완성 · 관측 · 배포 직전 검증”까지 한 번에 정리해 드릴게요.
요청하신 대로 Application Insights(앱인사이트) 로그와 LangSmith/LangFuse 이벤트도 넣었습니다.
(아래 코드는 바로 붙여 넣어 동작하도록 최소 예제로 정리했어요.)

3일차 목표

Streamlit UI에서 벡터 검색 + QA 동작

**Function(App)**과 Streamlit 양쪽에 관측(Observability) 추가

Application Insights(오픈텔레메트리 기반 스팬/로그)

LangSmith/LangFuse 추적/이벤트

엔드투엔드 테스트 & 운영 팁

3.1 Function(App) — 텔레메트리 + 일관 필드 + 예외 로그
(1) 의존성

backend/azure_function/log_uploader/requirements.txt에 추가:

azure-monitor-opentelemetry
langfuse
langsmith

(2) 환경변수 (로컬/운영 공통 키)

APPLICATIONINSIGHTS_CONNECTION_STRING

LANGCHAIN_TRACING_V2=true, LANGSMITH_API_KEY=<your_langsmith_key>

LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (원하실 때)

(이미 있으신) AZURE_SEARCH_*, AZURE_OPENAI_*

local.settings.json 예시는 이전에 드린 것 + 아래 키들 추가만 하면 됩니다.

(3) function_app.py 변경 포인트만 추가

v2 프로그래밍 모델(데코레이터) 기준

import logging, os, re, json, uuid, datetime
import azure.functions as func

# --- Application Insights(OpenTelemetry) 구성 ---
from azure.monitor.opentelemetry import configure_azure_monitor
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))

from opentelemetry import trace
tracer = trace.get_tracer("log_ingestor")

# --- LangFuse / LangSmith (선택) ---
from contextlib import suppress
lf, ls_client = None, None
with suppress(Exception):
    from langfuse import Langfuse
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        lf = Langfuse()  # 환경변수로 자동 구성

with suppress(Exception):
    from langsmith import Client as LSClient
    if os.getenv("LANGSMITH_API_KEY"):
        ls_client = LSClient()

# --- Azure Search / Embeddings: (이미 구성해두신 것과 동일) ---
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import AzureOpenAIEmbeddings

search_client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["SEARCH_INDEX_NAME"],
    credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
)
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)

app = func.FunctionApp()

@app.function_name(name="LogTrigger")
@app.blob_trigger(arg_name="myblob", path="log-upload/{name}", connection="AzureWebJobsStorage")
def log_trigger(myblob: func.InputStream):
    # 스팬 시작: 이 블롭 처리 전체를 하나의 트랜잭션으로 추적
    with tracer.start_as_current_span("ingest_blob") as span:
        span.set_attribute("blob.name", myblob.name)
        span.set_attribute("blob.size_bytes", myblob.length or 0)

        content = myblob.read().decode("utf-8")
        # 정규식 매칭 (예시)
        patterns = [r"Exception", r"Timeout", r"ERROR"]
        matches = [m for p in patterns for m in re.findall(p, content)]

        # 파일명 통일(베이스명만 저장 권장)
        base_name = os.path.basename(myblob.name)

        # LangFuse trace (선택)
        lf_trace = None
        if lf:
            with suppress(Exception):
                lf_trace = lf.trace(name="ingest_log", input={"filename": base_name})
                lf_trace.event(name="regex_matches",
                               metadata={"match_count": len(matches), "patterns": patterns})

        # LangSmith run (선택)
        ls_run = None
        if ls_client:
            with suppress(Exception):
                ls_run = ls_client.create_run(
                    name="ingest_log",
                    run_type="chain",
                    inputs={"filename": base_name, "size": myblob.length},
                    tags=["ingestion"]
                )

        # 임베딩 → 색인
        vector = embeddings.embed_documents([content])[0]
        doc = {
            "id": str(uuid.uuid4()),
            "content": content,
            "filename": base_name,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "content_vector": vector
        }

        search_client.merge_or_upload_documents([doc])  # 중복 방지
        logging.info(f"[Indexed] filename={base_name}, matches={len(matches)}")

        # AppInsights 스팬 이벤트
        span.add_event("IndexedToSearch", {
            "filename": base_name,
            "match_count": len(matches)
        })

        # LangFuse/LangSmith 마무리
        if lf_trace:
            with suppress(Exception):
                lf_trace.update(output={"doc_id": doc["id"], "match_count": len(matches)})
                lf.flush()

        if ls_run:
            with suppress(Exception):
                ls_client.update_run(
                    run_id=ls_run.id,
                    outputs={"doc_id": doc["id"], "match_count": len(matches)},
                    end_time=datetime.datetime.utcnow()
                )


이렇게 하면 Blob 업로드 → Function 트리거 → 색인 과정이 App Insights + LangFuse + LangSmith 모두에 남습니다.

3.2 Streamlit — QA UI + 텔레메트리
(1) 의존성

frontend/streamlit_app/requirements.txt:

streamlit
langchain
langchain-openai
langchain-community
azure-search-documents
python-dotenv
azure-monitor-opentelemetry
langfuse
langsmith

(2) 환경변수

.env(로컬) 또는 배포 시 환경설정에 아래 키 사용:

Azure OpenAI: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT

Azure Search: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, SEARCH_INDEX_NAME

App Insights: APPLICATIONINSIGHTS_CONNECTION_STRING

LangSmith: LANGCHAIN_TRACING_V2=true, LANGSMITH_API_KEY

LangFuse: LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

(3) app.py
import os, time
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

# --- App Insights(OpenTelemetry) ---
from azure.monitor.opentelemetry import configure_azure_monitor
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
from opentelemetry import trace
tracer = trace.get_tracer("streamlit_qa")

# --- LangFuse / LangSmith (optional) ---
from contextlib import suppress
lf, ls_client = None, None
with suppress(Exception):
    from langfuse import Langfuse
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        lf = Langfuse()
with suppress(Exception):
    from langsmith import Client as LSClient
    if os.getenv("LANGSMITH_API_KEY"):
        ls_client = LSClient()

# --- LLM / Retriever ---
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.chains import RetrievalQA

llm = AzureChatOpenAI(
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    temperature=0,
)

emb = AzureOpenAIEmbeddings(
    azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)

endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.getenv("SEARCH_INDEX_NAME", "log-index")

# Vector-only 기본 (버전 차이 흡수)
try:
    vectorstore = AzureSearch(
        azure_search_endpoint=endpoint,
        azure_search_key=key,
        index_name=index_name,
        embedding=emb,
        vector_field="content_vector",
        text_field="content",
    )
except TypeError:
    vectorstore = AzureSearch(
        azure_search_endpoint=endpoint,
        azure_search_key=key,
        index_name=index_name,
        embedding_function=emb.embed_query,
        vector_field="content_vector",
        text_field="content",
    )

retriever = vectorstore.as_retriever(k=4)

st.set_page_config(page_title="로그 분석 챗봇", page_icon="🪵")
st.title("🪵 로그 분석 챗봇")

with st.sidebar:
    st.subheader("검색 옵션")
    file_filter = st.text_input("파일명 필터 (예: 2025-09-23.log)", "")
    mode = st.selectbox("검색 모드", ["Vector", "Hybrid(가능 시)"], index=0)
    k = st.slider("Top-K", min_value=1, max_value=10, value=4)
    st.markdown("---")
    st.caption("LangSmith/LangFuse, AppInsights로 요청/응답이 추적됩니다.")

query = st.text_input("무엇이 궁금한가요?", placeholder="예: 9/23 로그에서 Exception/Timeout 요약해줘")

def apply_filter(r, fname: str):
    if not fname:
        return r
    # langchain-community azuresearch 버전마다 다르므로
    # 필터를 retriever 대신, 직접 similarity_search/hybrid_search 호출에서 처리하는 게 안전
    return None

if st.button("질의하기", type="primary", disabled=not query):
    t0 = time.time()
    # Telemetry span 시작
    with tracer.start_as_current_span("qa_query") as span:
        span.set_attribute("query", query)
        span.set_attribute("mode", mode)
        if file_filter:
            span.set_attribute("filter.filename", file_filter)

        # LangFuse/LangSmith trace
        lf_trace, ls_run = None, None
        if lf:
            with suppress(Exception):
                lf_trace = lf.trace(name="qa", input={"query": query, "mode": mode, "filename": file_filter or None})
        if ls_client:
            with suppress(Exception):
                ls_run = ls_client.create_run(name="streamlit_qa", run_type="chain",
                                              inputs={"query": query, "mode": mode, "filename": file_filter or None},
                                              tags=["qa"])

        # 검색 + QA
        try:
            # 간단 구현: Vector 기본 / Hybrid 시도 후 실패하면 Vector fallback
            sources = []
            if mode.startswith("Hybrid"):
                with suppress(Exception):
                    # 일부 버전에서만 제공: hybrid_search
                    sources = vectorstore.hybrid_search(query, k=k)
            if not sources:
                if file_filter:
                    # 파일 필터가 있으면 직접 similarity_search로 처리
                    sources = vectorstore.similarity_search(query, k=k, filter={"filename": file_filter})
                else:
                    sources = vectorstore.similarity_search(query, k=k)

            # QA 체인
            qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True, chain_type="stuff")
            result = qa.invoke({"query": query})
            answer = result["result"]
            used = result.get("source_documents", []) or sources

            # 출력
            st.subheader("답변")
            st.write(answer)
            st.subheader("출처")
            for i, d in enumerate(used[:k], 1):
                fname = getattr(d, "metadata", {}).get("filename") if hasattr(d, "metadata") else None
                snippet = d.page_content[:200].replace("\n", " ")
                st.write(f"[{i}] **{fname}** — {snippet}...")

            # 텔레메트리 기록
            span.set_attribute("latency_ms", int((time.time() - t0) * 1000))
            if lf_trace:
                with suppress(Exception):
                    lf_trace.update(output={"answer": answer[:300]})
                    lf_trace.event(name="qa_sources", metadata={"count": len(used), "filenames": [getattr(d, 'metadata', {}).get('filename') for d in used]})
                    lf.flush()
            if ls_run:
                with suppress(Exception):
                    ls_client.update_run(run_id=ls_run.id, outputs={"answer": answer[:300]}, end_time=None)

        except Exception as e:
            st.error(f"오류: {e}")
            span.record_exception(e)
            if lf_trace:
                with suppress(Exception):
                    lf_trace.event(name="qa_error", level="error", metadata={"error": str(e)})
                    lf.flush()
            if ls_run:
                with suppress(Exception):
                    ls_client.update_run(run_id=ls_run.id, error=str(e))


기본은 벡터 검색, 가능하면 하이브리드도 시도합니다(버전 차로 실패하면 자동 벡터 fallback).
filename 필터는 인덱싱 시 filename을 베이스명으로 저장해 두셨으니 그대로 필터로 쓸 수 있습니다.

3.3 관측(Observability) — 확인하는 법
Application Insights (KQL 예시)

Function 인덱싱 완료 이벤트(우리 스팬/로그):

traces
| where message has "Indexed" or customDimensions["filename"] != ""
| order by timestamp desc


스팬 이름으로 보기:

traces
| where operation_Name == "ingest_blob" or operation_Name == "qa_query"
| order by timestamp desc


예외/오류만:

exceptions
| order by timestamp desc

LangSmith

LANGCHAIN_TRACING_V2=true + LANGSMITH_API_KEY 설정 후
LangSmith 웹 콘솔에서 프로젝트/런으로 확인(체인 이름: ingest_log, streamlit_qa).

LangFuse

LANGFUSE_* 키 설정 후
LangFuse 대시보드에서 Trace ingest_log/qa, Event regex_matches/qa_sources/qa_error 확인.

3.4 최종 체크리스트

 Function(App)에서 파일 업로드 시 로그/스팬/이벤트가 각 대시보드에 찍히는지

 Streamlit에서 질의 요청 시 스팬/이벤트가 찍히는지

 filename 필터로 원하는 파일만 검색되는지

 (원한다면) 청크 분할로 검색 품질 향상 (로그 라인 기준 split → 길이 800~1200자로 업로드)

 Function App 배포:
func azure functionapp publish <FUNCTION_APP_NAME>
App Settings에 위 환경변수 모두 등록

3.5 작은 개선 아이디어 (선택)

중복 방지를 더 강하게: id = f"{base_name}:{sha1(chunk)}" 형태 고정 + merge_or_upload

하이브리드 검색 공식화: Azure SDK의 SearchClient.search(search_text + vector_queries)로 구현

처리 상태 표시: Function에서 indexed:<filename> 로그를 남기고, Streamlit 측에서 Search로 폴링해 “처리 완료” 배지 표시

필요하시면 청크 분할 업로드 코드와 하이브리드 검색(REST/SDK) 정식 구현도 바로 붙여드릴게요.
여기까지 적용하면 3일차 목표(프론트 + 관측 + E2E) 완료입니다.