# ##########################################################################
# # Default 생성
# ##########################################################################

# # import logging
# # import azure.functions as func
# # import re
# # import json

# # app = func.FunctionApp()  # 새 프로그래밍 모델에서는 앱 인스턴스를 명시

# # @app.function_name(name="LogTrigger")
# # @app.blob_trigger(arg_name="myblob",
# #                   path="log-upload/{name}",
# #                   connection="AzureWebJobsStorage")
# # def log_trigger(myblob: func.InputStream):
# #     logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

# #     content = myblob.read().decode("utf-8")
# #     patterns = [r"Exception", r"Timeout", r"Connection refused", r"NullPointerException"]
# #     matches = []
# #     for p in patterns:
# #         matches.extend(re.findall(p, content))

# #     summary = {
# #         "filename": myblob.name,
# #         "match_count": len(matches),
# #         "matched_patterns": matches
# #     }
# #     logging.info(f"Match Summary: {json.dumps(summary, indent=2)}")

# ##########################################################################
# # 수정 OpenAIEmbeddings => AzureOpenAIEmbeddings
# ##########################################################################
# import logging
# import azure.functions as func
# import re, json, os, uuid, datetime
# from azure.core.credentials import AzureKeyCredential
# from azure.search.documents import SearchClient
# from openai import OpenAI

# app = func.FunctionApp()

# # Azure Search 클라이언트
# search_client = SearchClient(
#     endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
#     index_name=os.environ["SEARCH_INDEX_NAME"],
#     credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
# )

# # OpenAI 임베딩
# # from langchain_openai import OpenAIEmbeddings
# # embeddings = OpenAIEmbeddings(model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"), api_key=os.getenv("AZURE_OPENAI_API_KEY"))

# from langchain_openai import AzureOpenAIEmbeddings
# embeddings = AzureOpenAIEmbeddings(
#     azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
#     azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
#     api_key=os.environ["AZURE_OPENAI_API_KEY"],
#     api_version=os.environ["AZURE_OPENAI_API_VERSION"],
# )


# @app.function_name(name="LogTrigger")
# @app.blob_trigger(arg_name="myblob", path="log-upload/{name}", connection="AzureWebJobsStorage")
# def log_trigger(myblob: func.InputStream):
#     logging.info(f"Processing blob: {myblob.name}")
#     content = myblob.read().decode("utf-8")

#     # 정규식 탐지
#     patterns = [r"Exception", r"Timeout", r"ERROR"]
#     matches = []
#     for p in patterns:
#         matches.extend(re.findall(p, content))
#     logging.info(f"Match Summary: {matches}")

#     # 벡터 생성 후 업로드
#     vector = embeddings.embed_documents([content])[0]
#     doc = {
#         "id": str(uuid.uuid4()),
#         "content": content,
#         "filename": myblob.name,
#         "timestamp": datetime.datetime.utcnow().isoformat(),
#         "content_vector": vector
#     }
#     search_client.upload_documents([doc])
#     logging.info("Uploaded to Azure Search")



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
