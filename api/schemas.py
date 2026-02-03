"""
API 스키마 정의

Request/Response 모델을 정의합니다.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ===== 공통 응답 =====
class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field(description="서버 상태")
    timestamp: datetime = Field(description="응답 시간")
    version: str = Field(description="API 버전")


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(default=None, description="상세 정보")


# ===== 자서전 생성 =====
class AutobiographyRequest(BaseModel):
    """자서전 생성 요청"""
    transcript: str = Field(
        description="일대기 텍스트 (음성 변환 결과 또는 직접 입력)",
        min_length=100,
        examples=["저는 1955년 경상북도 안동에서 태어났습니다..."]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcript": "저는 김영희라고 합니다. 1955년 경상북도 안동의 작은 마을에서 태어났습니다..."
            }
        }


class ChapterResponse(BaseModel):
    """챕터 응답"""
    period: str = Field(description="인생 시기")
    title: str = Field(description="챕터 제목")
    content: str = Field(description="챕터 내용")
    age_range: Optional[str] = Field(default=None, description="나이 범위")


class AutobiographyResponse(BaseModel):
    """자서전 생성 응답"""
    success: bool = Field(description="성공 여부")
    title: str = Field(description="자서전 제목")
    author_name: str = Field(description="저자 이름")
    prologue: str = Field(description="프롤로그")
    chapters: List[ChapterResponse] = Field(description="챕터 목록")
    epilogue: str = Field(description="에필로그")
    key_themes: List[str] = Field(description="핵심 주제들")
    life_lessons: List[str] = Field(description="인생의 교훈들")
    generated_at: datetime = Field(description="생성 시간")


# ===== 음성 변환 =====
class TranscriptionRequest(BaseModel):
    """음성 변환 요청 (파일 업로드는 Form으로 처리)"""
    language: str = Field(default="ko", description="오디오 언어")


class TranscriptionResponse(BaseModel):
    """음성 변환 응답"""
    success: bool = Field(description="성공 여부")
    transcript: str = Field(description="변환된 텍스트")
    duration_seconds: Optional[float] = Field(default=None, description="오디오 길이(초)")


# ===== 작업 상태 (비동기 처리용) =====
class JobStatus(BaseModel):
    """작업 상태"""
    job_id: str = Field(description="작업 ID")
    status: str = Field(description="상태 (pending, processing, completed, failed)")
    progress: Optional[int] = Field(default=None, description="진행률 (0-100)")
    result: Optional[AutobiographyResponse] = Field(default=None, description="결과 (완료 시)")
    error: Optional[str] = Field(default=None, description="에러 메시지 (실패 시)")
    created_at: datetime = Field(description="생성 시간")
    updated_at: datetime = Field(description="갱신 시간")


class JobCreateResponse(BaseModel):
    """작업 생성 응답"""
    job_id: str = Field(description="작업 ID")
    status: str = Field(description="상태")
    message: str = Field(description="메시지")
