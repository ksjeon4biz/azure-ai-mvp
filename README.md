# azure-ai-mvp

✅ 목표 요약

입력: 매일 생성되는 서버 로그 파일 (.log, .txt, .json 등)

처리: Azure Function이 로그 업로드 감지 → 특정 정규식 탐지 → RAG 벡터화

검색: RAG 기반 챗봇이 Streamlit에서 로그 기반 질의 응답 제공

보안: 내부 데이터로만 학습, 외부 유출 없음

목표: 전체 흐름 구성과 Azure 리소스 준비

1.1. 프로젝트 구조 설계
azure-ai-mvp/

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
