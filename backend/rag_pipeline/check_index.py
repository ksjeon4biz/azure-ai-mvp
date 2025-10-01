from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
import os
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())

search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
search_key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.environ["SEARCH_INDEX_NAME"]

client = SearchIndexClient(
    endpoint=search_endpoint,
    credential=AzureKeyCredential(search_key)
)

index = client.get_index(index_name)
print(f"Index Name: {index.name}")
print("Fields:")
for f in index.fields:
    print(f"  - {f.name} ({f.type})")
