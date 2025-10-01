import logging, os, re, json, uuid, datetime
import azure.functions as func
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

# --- App Insights ---
from azure.monitor.opentelemetry import configure_azure_monitor
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))

from opentelemetry import trace
tracer = trace.get_tracer("log_ingestor")

# --- LangFuse / LangSmith ---
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

# --- Azure Search / Embeddings ---
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import AzureOpenAIEmbeddings

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("SEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

app = func.FunctionApp()

@app.function_name(name="LogTrigger")
@app.blob_trigger(arg_name="myblob", path="log-upload/{name}", connection="AZURE_STORAGE_CONNECTION")
def log_trigger(myblob: func.InputStream):
    with tracer.start_as_current_span("ingest_blob") as span:
        span.set_attribute("blob.name", myblob.name)
        span.set_attribute("blob.size_bytes", myblob.length or 0)

        content = myblob.read().decode("utf-8")
        patterns = [r"Exception", r"Timeout", r"ERROR"]
        matches = [m for p in patterns for m in re.findall(p, content)]
        base_name = os.path.basename(myblob.name)

        # LangFuse / LangSmith trace
        lf_trace = None
        if lf:
            with suppress(Exception):
                lf_trace = lf.trace(name="ingest_log", input={"filename": base_name})
                lf_trace.event(name="regex_matches",
                               metadata={"match_count": len(matches), "patterns": patterns})

        ls_run = None
        if ls_client:
            with suppress(Exception):
                ls_run = ls_client.create_run(
                    name="ingest_log", run_type="chain",
                    inputs={"filename": base_name, "size": myblob.length}, tags=["ingestion"]
                )

        # 임베딩 + 색인
        vector = embeddings.embed_documents([content])[0]
        doc = {
            "id": str(uuid.uuid4()),
            "content": content,
            "filename": base_name,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "content_vector": vector
        }

        search_client.merge_or_upload_documents([doc])
        logging.info(f"[Indexed] filename={base_name}, matches={len(matches)}")

        span.add_event("IndexedToSearch", {
            "filename": base_name,
            "match_count": len(matches)
        })

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
