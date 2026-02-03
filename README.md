
## 📦 설치

### 1. 저장소 클론

```bash
git clone https://github.com/your-repo/gladtosenior_backend.git
cd gladtosenior_backend
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

또는 uv 사용:

```bash
uv pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집하여 OpenAI API 키 설정
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

## 🚀 서버 실행

### 개발 서버

```bash
# uvicorn으로 실행 (자동 리로드)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 또는 python으로 직접 실행
python app.py
```

### 프로덕션 서버

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```
