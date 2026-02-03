"""
FastAPI 애플리케이션

자서전 생성 API 서버
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 환경 변수 로드
load_dotenv()

from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    print("🚀 자서전 생성 API 서버 시작")
    
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 경고: OPENAI_API_KEY가 설정되지 않았습니다.")
    else:
        print("✅ OpenAI API 키 확인됨")
    
    yield
    
    # 종료 시
    print("👋 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="자서전 생성 API",
    description="""
## Deep Agent 기반 자서전 생성 서비스

음성 또는 텍스트로 입력된 일대기를 분석하여, 
인생 시기별 전문 에이전트들이 협력하여 완성도 높은 자서전을 생성합니다.

### 주요 기능
- **자서전 생성**: 텍스트 입력을 받아 자서전 생성
- **음성 변환**: 음성 파일을 텍스트로 변환
- **비동기 처리**: 긴 작업을 백그라운드에서 처리

### 에이전트 구성
- 유년기 에이전트 (0-12세)
- 청년기 에이전트 (13-29세)
- 중년기 에이전트 (30-49세)
- 장년기 에이전트 (50-64세)
- 노년기 에이전트 (65세 이상)
- 오케스트레이션 에이전트 (통합 관리)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:5173",  # Vite 개발 서버
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # 프로덕션 도메인 추가
        # "https://your-frontend-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 라우터 등록
app.include_router(router, prefix="/api/v1", tags=["autobiography"])


@app.get("/", tags=["root"])
async def root():
    """루트 엔드포인트"""
    return {
        "service": "자서전 생성 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    # 서버 실행
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드
    )
