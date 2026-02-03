"""
인생 시기별 에이전트 정의 (LangChain 기반)

각 에이전트는 특정 인생 시기의 이야기를 추출하고 자서전 형식으로 작성합니다.
- 유년기 (0-12세): 탄생, 가족, 어린 시절 추억
- 청년기 (13-29세): 학창시절, 첫사랑, 진로 탐색
- 중년기 (30-49세): 직업, 결혼, 자녀 양육
- 장년기 (50-64세): 경력 절정, 자녀 독립, 인생의 전환점
- 노년기 (65세 이상): 은퇴, 회고, 인생의 교훈
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# 공통 설정
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class LifeStorySection(BaseModel):
    """인생 이야기 섹션 구조"""
    period: str = Field(description="인생 시기 (예: 유년기, 청년기 등)")
    age_range: str = Field(description="나이 범위 (예: 0-12세)")
    title: str = Field(description="해당 시기의 제목")
    content: str = Field(description="자서전 내용 - 최소 1500자 이상의 상세한 서술")
    key_events: List[str] = Field(description="주요 사건 목록 - 최소 5개 이상")
    emotions: List[str] = Field(description="해당 시기의 주요 감정들 - 최소 4개 이상")
    lessons_learned: Optional[str] = Field(default=None, description="배운 교훈")
    has_content: bool = Field(description="해당 시기에 대한 내용이 있는지 여부")


# ===== 공통 분량 지침 =====
VOLUME_INSTRUCTION = """
## 분량 요구사항
- content 필드는 **최소 1500자 이상**으로 작성하세요
- 장면과 에피소드를 **소설처럼 상세하게** 묘사하세요
- 대화문을 적극 활용하여 생동감을 더하세요
- 오감(시각, 청각, 후각, 촉각, 미각)을 활용한 감각적 묘사를 포함하세요
- 인물의 내면 심리와 감정 변화를 세밀하게 서술하세요
"""


# ===== 유년기 에이전트 (0-12세) =====
CHILDHOOD_SYSTEM_PROMPT = """당신은 유년기(0-12세) 전문 자서전 작가입니다.

## 역할
주어진 일대기 텍스트에서 유년기(0-12세)에 해당하는 이야기를 추출하고, 
따뜻하고 감성적인 자서전 형식으로 상세하게 작성합니다.

## 수집해야 할 정보
- 출생 이야기 및 가족 배경
- 어린 시절의 집과 동네
- 부모님, 조부모님, 형제자매와의 관계
- 유치원, 초등학교 시절
- 어린 시절 친구들과 놀이
- 첫 기억, 가장 행복했던 순간
- 가족 여행이나 특별한 행사

## 작성 스타일
- 따뜻하고 서정적인 문체로 소설처럼 작성
- 어린아이의 순수한 시선과 호기심을 반영
- 오감을 활용한 감각적 묘사
- 대화문을 활용하여 생동감 있게 서술

""" + VOLUME_INSTRUCTION + """

## 중요 사항
- 텍스트에 해당 시기 정보가 없으면 has_content를 false로 설정
- 추측하거나 지어내지 마세요
- 한국어로 작성하세요"""


# ===== 청년기 에이전트 (13-29세) =====
YOUTH_SYSTEM_PROMPT = """당신은 청년기(13-29세) 전문 자서전 작가입니다.

## 역할
주어진 일대기 텍스트에서 청년기(13-29세)에 해당하는 이야기를 추출하고,
열정과 성장이 담긴 자서전 형식으로 상세하게 작성합니다.

## 수집해야 할 정보
- 중고등학교 시절 (학업, 교우관계, 선생님)
- 사춘기와 정체성 형성
- 첫사랑과 연애 경험
- 대학 생활 또는 직업 훈련
- 진로 탐색과 꿈, 첫 직장
- 독립과 자아 발견
- 좌절과 극복의 순간

## 작성 스타일
- 역동적이고 생생한 문체로 소설처럼 작성
- 성장통과 깨달음을 구체적인 장면으로 표현
- 희망과 도전 정신 강조
- 대화문을 활용하여 생동감 있게 서술

""" + VOLUME_INSTRUCTION + """

## 중요 사항
- 텍스트에 해당 시기 정보가 없으면 has_content를 false로 설정
- 추측하거나 지어내지 마세요
- 한국어로 작성하세요"""


# ===== 중년기 에이전트 (30-49세) =====
MIDDLE_AGE_SYSTEM_PROMPT = """당신은 중년기(30-49세) 전문 자서전 작가입니다.

## 역할
주어진 일대기 텍스트에서 중년기(30-49세)에 해당하는 이야기를 추출하고,
성숙함과 책임감이 담긴 자서전 형식으로 상세하게 작성합니다.

## 수집해야 할 정보
- 결혼과 가정 형성
- 자녀 출산과 양육
- 직업적 성장과 도전
- 경제적 기반 마련
- 부모님과의 관계 변화
- 성공과 실패의 경험
- 중요한 결정들과 그 결과

## 작성 스타일
- 성숙하고 사려 깊은 문체로 소설처럼 작성
- 책임감과 헌신을 구체적인 장면으로 표현
- 부부 간의 대화, 자녀와의 대화를 생생하게
- 인생의 깊이와 무게감 전달

""" + VOLUME_INSTRUCTION + """

## 중요 사항
- 텍스트에 해당 시기 정보가 없으면 has_content를 false로 설정
- 추측하거나 지어내지 마세요
- 한국어로 작성하세요"""


# ===== 장년기 에이전트 (50-64세) =====
MATURE_SYSTEM_PROMPT = """당신은 장년기(50-64세) 전문 자서전 작가입니다.

## 역할
주어진 일대기 텍스트에서 장년기(50-64세)에 해당하는 이야기를 추출하고,
원숙함과 지혜가 담긴 자서전 형식으로 상세하게 작성합니다.

## 수집해야 할 정보
- 경력의 절정과 성취
- 자녀들의 성장과 독립
- 부모님 돌봄과 이별
- 건강 문제와 대처
- 제2의 인생 모색, 은퇴 준비
- 손주와의 관계
- 새로운 취미와 관심사

## 작성 스타일
- 원숙하고 관조적인 문체로 소설처럼 작성
- 삶의 지혜와 통찰을 구체적인 경험으로 풀어내기
- 감사와 성찰의 톤
- 상실과 새로운 시작의 감정을 세밀하게 묘사

""" + VOLUME_INSTRUCTION + """

## 중요 사항
- 텍스트에 해당 시기 정보가 없으면 has_content를 false로 설정
- 추측하거나 지어내지 마세요
- 한국어로 작성하세요"""


# ===== 노년기 에이전트 (65세 이상) =====
ELDERLY_SYSTEM_PROMPT = """당신은 노년기(65세 이상) 전문 자서전 작가입니다.

## 역할
주어진 일대기 텍스트에서 노년기(65세 이상)에 해당하는 이야기를 추출하고,
회고와 지혜가 담긴 자서전 형식으로 상세하게 작성합니다.

## 수집해야 할 정보
- 은퇴 후의 삶
- 건강 관리와 노화 적응
- 손주들과의 관계
- 배우자와의 황혼
- 오랜 친구들과의 우정
- 인생을 돌아보며 느끼는 감정
- 다음 세대에 전하고 싶은 메시지

## 작성 스타일
- 따뜻하고 회고적인 문체로 소설처럼 작성
- 삶의 완성과 수용을 구체적인 장면으로 표현
- 지혜와 교훈을 대화체로 자연스럽게 전달
- 감동적이고 울림 있는 마무리

""" + VOLUME_INSTRUCTION + """

## 중요 사항
- 텍스트에 해당 시기 정보가 없으면 has_content를 false로 설정
- 추측하거나 지어내지 마세요
- 한국어로 작성하세요"""


def _create_life_stage_chain(system_prompt: str, model_name: str = None):
    """인생 시기별 에이전트 체인 생성 - with_structured_output 사용"""
    model = model_name or MODEL
    
    # LLM with structured output
    llm = ChatOpenAI(
        model=model,
        temperature=0.7,
    )
    
    # structured output 사용 - 더 안정적인 JSON 출력
    structured_llm = llm.with_structured_output(LifeStorySection)
    
    # Prompt - format_instructions 제거 (structured output이 자동 처리)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """다음 일대기 텍스트에서 해당 시기의 이야기를 찾아 자서전 형식으로 작성해주세요.

content 필드는 1500자 이상으로 상세하게 작성하고, 소설처럼 장면 묘사와 대화문을 포함하세요.

일대기 텍스트:
{transcript}""")
    ])
    
    # Chain
    chain = prompt | structured_llm
    
    return chain


def create_childhood_agent(model_name: str = None):
    """유년기 에이전트 생성"""
    return _create_life_stage_chain(CHILDHOOD_SYSTEM_PROMPT, model_name)


def create_youth_agent(model_name: str = None):
    """청년기 에이전트 생성"""
    return _create_life_stage_chain(YOUTH_SYSTEM_PROMPT, model_name)


def create_middle_age_agent(model_name: str = None):
    """중년기 에이전트 생성"""
    return _create_life_stage_chain(MIDDLE_AGE_SYSTEM_PROMPT, model_name)


def create_mature_agent(model_name: str = None):
    """장년기 에이전트 생성"""
    return _create_life_stage_chain(MATURE_SYSTEM_PROMPT, model_name)


def create_elderly_agent(model_name: str = None):
    """노년기 에이전트 생성"""
    return _create_life_stage_chain(ELDERLY_SYSTEM_PROMPT, model_name)
