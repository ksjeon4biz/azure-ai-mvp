import os, uuid, datetime
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()

# 공용 설정/클라이언트
ROOT = Path(__file__).resolve().parents[1]  # 프로젝트 루트
LOG_DIR = Path(os.getenv("LOG_DIR", ROOT / "data" / "logs"))

AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
AZURE_SEARCH_KEY = os.environ["AZURE_SEARCH_KEY"]
INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "log-index")

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY),
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)

EXPECTED_DIMS = 1536

def upload_log(filename: str, content: str):
    vec = embeddings.embed_documents([content])[0]
    if len(vec) != EXPECTED_DIMS:
        raise ValueError(f"Embedding dims {len(vec)} != index dims {EXPECTED_DIMS}")
    doc = {
        "id": str(uuid.uuid4()),
        "content": content,
        "filename": filename,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "content_vector": vec,
    }
    search_client.upload_documents([doc])

def main():
    target = LOG_DIR / "2025-09-25.log"   # 필요 시 인자/글롭으로 확장
    with target.open("r", encoding="utf-8") as f:
        text = f.read()
    upload_log(target.name, text)
    print(f"Uploaded {target.name}")

if __name__ == "__main__":
    main()
