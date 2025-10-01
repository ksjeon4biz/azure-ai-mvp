import os, time
import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


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

        try:
            # retriever에 file_filter 적용 (옵션1 핵심 부분)
            # --- retriever 생성 ---
            search_kwargs = {}
            if file_filter:
                search_kwargs["filter"] = {"filename": file_filter}
            retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

            # --- hybrid 검색 (필요한 경우) ---
            sources = []
            if mode.startswith("Hybrid"):
                with suppress(Exception):
                    sources = vectorstore.hybrid_search(query, k=k)  # ✅ k는 여기서만!


            # QA 체인
            qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True, chain_type="stuff")
            result = qa.invoke({"query": query})
            answer = result["result"]
            used = result.get("source_documents", [])

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
