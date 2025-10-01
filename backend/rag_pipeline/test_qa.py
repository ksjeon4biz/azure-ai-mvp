# --- optional: stdlib asyncio pre-load (무해, 문제 예방) ---
import importlib, asyncio  # noqa
importlib.invalidate_caches()

import os
from dotenv import find_dotenv, load_dotenv
from contextlib import suppress
import gc

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv())

def build_llm_and_embeddings():
    llm = AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        temperature=0,
    )
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )
    return llm, embeddings

def build_vectorstore(embeddings):
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_KEY"]
    index_name = os.getenv("SEARCH_INDEX_NAME", "log-index")

    try:
        # 신형 시그니처
        return AzureSearch(
            azure_search_endpoint=endpoint,
            azure_search_key=key,
            index_name=index_name,
            embedding=embeddings,
            vector_field="content_vector",
            text_field="content",
        )
    except TypeError:
        # 구형 시그니처
        return AzureSearch(
            azure_search_endpoint=endpoint,
            azure_search_key=key,
            index_name=index_name,
            embedding_function=embeddings.embed_query,
            vector_field="content_vector",
            text_field="content",
        )

def main():
    # (윈도우일 때만) 이벤트 루프 폴리시 보장 – 필요 시 주석 해제
    # if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    llm, embeddings = build_llm_and_embeddings()
    vectorstore = build_vectorstore(embeddings)

    retriever = vectorstore.as_retriever(k=4)  # search_kwargs에 k 넣지 말 것
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
    )

    query = os.getenv("QA_QUERY", "최근 업로드된 로그에서 Exception/Timeout 관련 이슈를 요약해줘")
    result = qa.invoke({"query": query})

    print("\n=== Answer ===")
    print(result["result"])

    print("\n=== Sources ===")
    for i, doc in enumerate(result.get("source_documents", []), 1):
        fname = getattr(doc, "metadata", {}).get("filename") if hasattr(doc, "metadata") else None
        print(f"[{i}] filename={fname} | snippet={doc.page_content[:120]}...")

    # ---- 명시적 정리 (중요) ----
    with suppress(Exception):
        del retriever, qa, vectorstore, embeddings, llm
    gc.collect()

if __name__ == "__main__":
    main()
