# PDF RAG Chatbot (Streamlit)

업로드한 **PDF 문서 내용**을 기반으로 질문하면 답변해주는 **문서 기반 Q&A 웹앱(RAG)** 입니다.  
Streamlit UI + LangChain + FAISS + OpenAI Embeddings/Chat 모델로 동작합니다.

---

## 1) 준비물

- Python **3.10+** 권장
- OpenAI API Key

프로젝트 구조 예시:

```
project/
 ├─ app.py
 ├─ README.md
 ├─ requirements.txt
 └─ .env
```

---

## 2) 설치 (가상환경 권장)

### (1) 가상환경 생성/활성화

#### Windows (PowerShell)
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux / Windows
```bash
conda create -n py310 python=3.10
conda activate py310
```

### (2) requirements 설치
```bash
pip install -r requirements.txt
```

---

## 3) API Key 설정 (.env)

프로젝트 루트에 `.env` 파일을 만들고 아래처럼 저장합니다.

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ `.env` 파일은 GitHub에 업로드하지 마세요.

---

## 4) 실행

```bash
streamlit run app.py
```

브라우저에서 보통 아래 주소로 접속됩니다.

- http://localhost:8501

---

## 5) 사용 방법

1. 웹페이지에서 **PDF 파일 업로드**
2. **📌 PDF 인덱싱(벡터DB 생성)** 버튼 클릭  
   - PDF 로드 → 청크 분할 → 임베딩 생성 → FAISS 인덱싱
3. 질문 입력 후 **질문하기** 클릭
4. (옵션) **검색 결과 보기**로 Top-k 문서 조각 확인 가능

---

## 6) 설정(사이드바)

- **Embedding 모델**: 기본 `text-embedding-3-small`
- **Chat 모델**: 기본 `gpt-5-nano`
- **검색 Top-k**: 검색해서 prompt에 넣는 문서 조각 개수
- **chunk_size / chunk_overlap**: 문서 청크 분할 파라미터
  - 일반적으로 chunk_size↑ = 문맥 길어짐(정보 많음) / 검색 정밀도↓ 가능
  - overlap↑ = 문맥 연결성↑ / 인덱싱 비용↑ 가능

---

## 7) Troubleshooting

### Q1. `OPENAI_API_KEY` 관련 에러
- `.env`가 프로젝트 루트에 있는지 확인
- 키가 정확한지 확인 (앞뒤 공백/따옴표 주의)
- `python-dotenv`가 설치되어 있는지 확인

### Q2. PDF 텍스트가 비거나 한글이 깨짐
- 스캔본(이미지 기반) PDF는 `PyPDFLoader`로 텍스트 추출이 잘 안 될 수 있습니다.
  - 이 경우 OCR 기반 파이프라인이 필요합니다.

### Q3. 인덱싱이 느림
- chunk_size를 키우거나, k를 줄여보세요.
- 문서가 크면 처음 인덱싱에 시간이 걸리는 게 정상입니다.
- (개선) FAISS 인덱스 저장/로드(캐싱) 추가 가능