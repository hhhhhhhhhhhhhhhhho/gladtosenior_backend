"""
API 라우트 정의

FastAPI 엔드포인트를 정의합니다.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from .schemas import (
    AutobiographyRequest,
    AutobiographyResponse,
    ChapterResponse,
    TranscriptionResponse,
    HealthResponse,
    ErrorResponse,
    JobStatus,
    JobCreateResponse,
)
from autobiography_agents import run_autobiography_generation
from services import AudioTranscriber, FileHandler


router = APIRouter()

# 작업 저장소 (실제 운영에서는 Redis 등 사용)
job_store: dict = {}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서버 상태를 확인합니다.",
)
async def health_check():
    """서버 헬스 체크"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )


@router.post(
    "/autobiography/generate",
    response_model=AutobiographyResponse,
    summary="자서전 생성 (동기)",
    description="텍스트를 입력받아 자서전을 생성합니다. 처리 시간이 길 수 있습니다.",
    responses={
        200: {"description": "자서전 생성 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    }
)
async def generate_autobiography(request: AutobiographyRequest):
    """
    자서전 생성 (동기 방식)
    
    - 텍스트 입력을 받아 5개 시기별 에이전트가 병렬로 처리
    - 처리 시간: 약 2-5분 소요
    """
    try:
        # 자서전 생성
        result = await run_autobiography_generation(request.transcript)
        
        # 응답 변환
        chapters = []
        if hasattr(result, 'chapters') and result.chapters:
            for ch in result.chapters:
                chapters.append(ChapterResponse(
                    period=ch.period if hasattr(ch, 'period') else ch.get('period', ''),
                    title=ch.title if hasattr(ch, 'title') else ch.get('title', ''),
                    content=ch.content if hasattr(ch, 'content') else ch.get('content', ''),
                    age_range=None,
                ))
        
        return AutobiographyResponse(
            success=True,
            title=result.title,
            author_name=result.author_name,
            prologue=result.prologue,
            chapters=chapters,
            epilogue=result.epilogue,
            key_themes=result.key_themes,
            life_lessons=result.life_lessons,
            generated_at=datetime.now(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"자서전 생성 중 오류 발생: {str(e)}"
        )


@router.post(
    "/autobiography/generate/async",
    response_model=JobCreateResponse,
    summary="자서전 생성 (비동기)",
    description="자서전 생성 작업을 백그라운드에서 실행합니다. job_id로 상태를 조회할 수 있습니다.",
)
async def generate_autobiography_async(
    request: AutobiographyRequest,
    background_tasks: BackgroundTasks
):
    """
    자서전 생성 (비동기 방식)
    
    - 작업을 백그라운드에서 실행
    - 반환된 job_id로 /jobs/{job_id} 에서 상태 조회
    """
    job_id = str(uuid.uuid4())
    
    # 작업 초기화
    job_store[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        result=None,
        error=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        process_autobiography_job,
        job_id,
        request.transcript
    )
    
    return JobCreateResponse(
        job_id=job_id,
        status="pending",
        message="자서전 생성 작업이 시작되었습니다. /jobs/{job_id} 에서 상태를 확인하세요."
    )


async def process_autobiography_job(job_id: str, transcript: str):
    """백그라운드 자서전 생성 작업"""
    try:
        # 상태 업데이트: 처리 중
        job_store[job_id].status = "processing"
        job_store[job_id].progress = 10
        job_store[job_id].updated_at = datetime.now()
        
        # 자서전 생성
        result = await run_autobiography_generation(transcript)
        
        # 응답 변환
        chapters = []
        if hasattr(result, 'chapters') and result.chapters:
            for ch in result.chapters:
                chapters.append(ChapterResponse(
                    period=ch.period if hasattr(ch, 'period') else ch.get('period', ''),
                    title=ch.title if hasattr(ch, 'title') else ch.get('title', ''),
                    content=ch.content if hasattr(ch, 'content') else ch.get('content', ''),
                    age_range=None,
                ))
        
        # 상태 업데이트: 완료
        job_store[job_id].status = "completed"
        job_store[job_id].progress = 100
        job_store[job_id].result = AutobiographyResponse(
            success=True,
            title=result.title,
            author_name=result.author_name,
            prologue=result.prologue,
            chapters=chapters,
            epilogue=result.epilogue,
            key_themes=result.key_themes,
            life_lessons=result.life_lessons,
            generated_at=datetime.now(),
        )
        job_store[job_id].updated_at = datetime.now()
        
    except Exception as e:
        # 상태 업데이트: 실패
        job_store[job_id].status = "failed"
        job_store[job_id].error = str(e)
        job_store[job_id].updated_at = datetime.now()


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatus,
    summary="작업 상태 조회",
    description="비동기 작업의 상태를 조회합니다.",
    responses={
        200: {"description": "작업 상태"},
        404: {"model": ErrorResponse, "description": "작업을 찾을 수 없음"},
    }
)
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    if job_id not in job_store:
        raise HTTPException(
            status_code=404,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )
    
    return job_store[job_id]


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="음성 파일 변환",
    description="음성 파일을 텍스트로 변환합니다.",
    responses={
        200: {"description": "변환 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 파일"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    }
)
async def transcribe_audio(
    file: UploadFile = File(..., description="오디오 파일 (mp3, wav, m4a 등)"),
    language: str = Form(default="ko", description="오디오 언어")
):
    """
    음성 파일을 텍스트로 변환
    
    - 지원 형식: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg, flac
    - 최대 파일 크기: 25MB (또는 약 10분)
    - 긴 파일은 자동으로 청크 분할 처리
    """
    # 파일 확장자 확인
    allowed_extensions = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.flac'}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다: {file_ext}. 지원 형식: {', '.join(allowed_extensions)}"
        )
    
    try:
        # 임시 파일 저장
        temp_dir = "./temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_ext}")
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        try:
            # 트랜스크립션
            transcriber = AudioTranscriber(language=language)
            transcript = await transcriber.transcribe(temp_path, show_progress=False)
            
            return TranscriptionResponse(
                success=True,
                transcript=transcript,
                duration_seconds=None  # pydub 없이는 길이 측정 불가
            )
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"음성 변환 중 오류 발생: {str(e)}"
        )


@router.post(
    "/autobiography/save",
    summary="자서전 파일 저장",
    description="생성된 자서전을 파일로 저장합니다.",
)
async def save_autobiography(response: AutobiographyResponse):
    """자서전을 파일로 저장"""
    try:
        file_handler = FileHandler()
        
        # 결과를 dict로 변환
        data = {
            "title": response.title,
            "author_name": response.author_name,
            "prologue": response.prologue,
            "chapters": [ch.model_dump() for ch in response.chapters],
            "epilogue": response.epilogue,
            "key_themes": response.key_themes,
            "life_lessons": response.life_lessons,
        }
        
        saved_files = file_handler.save_autobiography(data, response.author_name)
        
        return {
            "success": True,
            "saved_files": saved_files,
            "message": "자서전이 성공적으로 저장되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 저장 중 오류 발생: {str(e)}"
        )
