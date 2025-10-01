import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,  # ← 구체 알고리즘 클래스
)
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_KEY"]
index_name = os.environ.get("SEARCH_INDEX_NAME", "log-index")

client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# 1) 필드 정의 (중요: 속성명은 vector_search_dimensions / vector_search_profile_name)
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="filename", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SimpleField(name="timestamp", type=SearchFieldDataType.String, filterable=True, sortable=True),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,             # ← 올바른 명칭
        vector_search_profile_name="vprof_hnsw"    # ← 올바른 명칭
    ),
]

# 2) 벡터 검색 구성 (알고리즘 + 프로파일)
vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(name="hnsw_cfg")  # ← kind 자동으로 hnsw
    ],
    profiles=[
        VectorSearchProfile(name="vprof_hnsw", algorithm_configuration_name="hnsw_cfg")
    ],
)

index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)

# 기존 인덱스 삭제 후 생성(개발용)
try:
    client.delete_index(index_name)
    print(f"Deleted existing index {index_name}")
except Exception:
    pass

client.create_index(index)
print(f"Index {index_name} created!")
