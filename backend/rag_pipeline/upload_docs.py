import os, uuid, datetime
from dotenv import find_dotenv, load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv(find_dotenv())


AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME", "log-index")
LOG_DIR = os.getenv("LOG_DIR", "../data/logs")

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

def upload_log(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    vector = embeddings.embed_documents([content])[0]
    doc = {
        "id": str(uuid.uuid4()),
        "content": content,
        "filename": os.path.basename(file_path),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "content_vector": vector
    }

    result = search_client.merge_or_upload_documents([doc])
    print(f"Uploaded: {os.path.basename(file_path)} → {result[0].succeeded}")

if __name__ == "__main__":
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".log"):
            upload_log(os.path.join(LOG_DIR, fname))
