from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import os
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())
search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
search_key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.environ["SEARCH_INDEX_NAME"]

client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
)

count = client.get_document_count()
print(f"Total documents in index '{index_name}': {count}")
