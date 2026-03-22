# PDF RAG Chatbot (Streamlit)

업로드한 **PDF 문서 내용**을 기반으로 질문하면 답변해주는 **문서 기반 Q&A 웹앱(RAG)** 입니다.  
UI는 **Streamlit**, 검색은 **FAISS(Vector DB)**, 생성은 **OpenAI Chat 모델**, 문서 임베딩은 **OpenAI Embeddings**를 사용합니다.

또한 �� 프로젝트는 **대화 요약 메모리(Summary Memory)** 를 적용해, 이전 대화 내용을 “요약해서” 유지하며 다음 질문에 반영합니다.

---

## 1) 주요 기능

- PDF 업로드 후 **벡터DB(FAISS) 인덱싱**
- 질문 시 PDF에서 관련 문서 조각을 검색하여 답변하는 **RAG**
- **대화 요약 메모리(ConversationSummaryMemory)** 로 멀티턴 대화 지원  
  - 대화가 길어져도 전체를 저장하지 않고 **요약을 유지**
- 채팅 UI
  - 질문 입력 후 **Enter** 로 전송 가능
  - 입력창 옆에 **“질문” 버튼**으로도 전송 가능

---

## 2) 프로젝트 구조 예시

```
project/
 ├─ app.py
 ├─ README.md
 ├─ requirements.txt
 └─ .env
```

---

## 3) 요구 사항(Requirements)

- Python **3.10+** 권장
- OpenAI API Key

> 참고: 스캔본(이미지 기반) PDF는 텍스트 추출이 잘 안 될 수 있습니다(아래 Troubleshooting 참고).

---

## 4) 설치

### (1) 가상환경 생성/활성화 (권장)

#### Windows (PowerShell)
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

### (2) 패키지 설치
```bash
pip install -r requirements.txt
```

---

## 5) OpenAI API Key 설정 (.env)

프로젝트 루트에 `.env` 파일을 만들고 아래처럼 저장합니다.

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ `.env` 파일은 GitHub에 업로드하지 마세요.

---

## 6) 실행

프로젝트 루트에서 실행:

```bash
streamlit run app.py
```

정상 실행되면 브라우저가 열리며 보통 아래 주소로 접속됩니다.

- http://localhost:8501

---

## 7) 사용 방법

1. 웹페이지에서 **PDF 파일 업로드**
2. **📌 PDF 인덱싱(벡터DB 생성)** 버튼 클릭  
   - PDF 로드 → 청크 분할 → 임베딩 생성 → FAISS 인덱싱
3. 하단 채팅 입력창에 질문 입력
   - **Enter** 로 전송하거나
   - 오른쪽의 **“질문” 버튼**으로 전송
4. 답변이 채팅 형태로 출력됩니다.
5. (선택) 사이드바에서 **🧹 대화 초기화**로 요약 메모리/채팅을 초기화할 수 있습니다.

---

## 8) 설정(사이드바)

- **Embedding 모델**: 기본 `text-embedding-3-small`
- **Chat 모델**: 기본 `gpt-5-nano`
- **검색 Top-k**: 검색해서 prompt에 넣는 문서 조각 개수
- **chunk_size / chunk_overlap**: 문서 청크 분할 파라미터
  - `chunk_size`를 키우면 문맥이 길어지지만 검색 정밀도가 떨어질 수 있음
  - `chunk_overlap`을 키우면 문맥 연결성이 좋아지나 인덱싱 비용이 늘 수 있음

---

## 9) 대화 메모리(요약) 동작 방식

이 앱은 “이전 질문/답변 전체”를 그대로 프롬프트에 넣지 않고, LangChain의 **ConversationSummaryMemory**를 사용해 대화 내용을 **요약(summary) 형태로 유지**합니다.

- 장점: 긴 대화에서도 토큰/비용을 줄이며 맥락을 유지하기 쉬움
- 주의: 요약 업데이트를 위해 **추가 LLM 호출**이 발생할 수 있어 비용/지연이 약간 증가할 수 있음

---

## 10) Troubleshooting

### Q1. `OPENAI_API_KEY` 관련 에러가 나요
- `.env`가 프로젝트 루트에 있는지 확인
- 키가 정확한지 확인 (앞뒤 공백/따옴표 주의)
- 가상환경이 활성화된 상태에서 실행 중인지 확인

### Q2. `ConversationSummaryMemory import 실패`가 나요
LangChain 버전에 따라 메모리 클래스 위치가 달라질 수 있습니다.  
현재 `app.py`는 아래처럼 **여러 경로를 순차 시도**하도록 되어 있습니다.

- `from langchain.memory import ConversationSummaryMemory`
- 실패 시 `from langchain_classic.memory import ConversationSummaryMemory`

그래도 실패하면 아래 명령 결과를 확인해 주세요.

```bash
pip show langchain langchain-community langchain-openai
```

### Q3. PDF 텍스트가 비어있거나 한글이 깨져요
- 스캔본(이미지 기반) PDF는 `PyPDFLoader`로 텍스트 추출이 잘 안 될 수 있습니다.
- 이 경우 OCR(Tesseract, AWS Textract 등) 기반 파이프라인이 필요합니다.

### Q4. 인덱싱이 너무 느려요
- `chunk_size`를 키우거나, `k`를 줄여보세요.
- 문서가 크면 처음 인덱싱에 시간이 걸리는 것이 정상입니다.
- (개선 포인트) FAISS 인덱스 저장/로드(캐싱) 기능을 추가하면 재실행 시 빠릅니다.

---

## 11) 추가 개선 아이디어(선택)

- PDF 여러 개 업로드 + 통합 인덱싱
- 답변에 인용/출처(페이지 번호) 더 깔끔하게 표시
- FAISS 인덱스 디스크 저장/로드(재인덱싱 방지)
- 스캔 PDF 대응(OCR) 파이프라인 추가