"""
오케스트레이션 에이전트 (LangGraph 기반)

모든 인생 시기별 에이전트를 통합 관리하고,
최종 자서전을 생성하는 메인 오케스트레이터입니다.
"""

import os
import sys
import asyncio

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from typing import List, Optional, TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from .life_stage_agents import (
    create_childhood_agent,
    create_youth_agent,
    create_middle_age_agent,
    create_mature_agent,
    create_elderly_agent,
    LifeStorySection,
)


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class Chapter(BaseModel):
    """자서전 챕터"""
    period: str = Field(description="인생 시기 (예: 유년기)")
    title: str = Field(description="챕터 제목")
    content: str = Field(description="챕터 내용")


class AutobiographyResult(BaseModel):
    """최종 자서전 결과"""
    title: str = Field(description="자서전 제목")
    author_name: str = Field(description="저자(주인공) 이름")
    prologue: str = Field(description="서문/프롤로그")
    chapters: List[Chapter] = Field(description="각 인생 시기별 챕터")
    epilogue: str = Field(description="에필로그/맺음말")
    key_themes: List[str] = Field(description="자서전의 핵심 주제들")
    life_lessons: List[str] = Field(description="인생의 교훈들")


class AnalysisResult(BaseModel):
    """일대기 분석 결과"""
    author_name: str = Field(description="주인공 이름")
    birth_year: Optional[int] = Field(default=None, description="출생년도")
    current_age: Optional[int] = Field(default=None, description="현재 나이")
    summary: str = Field(description="일대기 요약")
    detected_periods: List[str] = Field(description="감지된 인생 시기들")
    main_themes: List[str] = Field(description="주요 테마들")


# ===== 상태 정의 =====
class AutobiographyState(TypedDict):
    """자서전 생성 상태"""
    transcript: str
    analysis: Optional[AnalysisResult]
    childhood_chapter: Optional[LifeStorySection]
    youth_chapter: Optional[LifeStorySection]
    middle_age_chapter: Optional[LifeStorySection]
    mature_chapter: Optional[LifeStorySection]
    elderly_chapter: Optional[LifeStorySection]
    final_autobiography: Optional[AutobiographyResult]
    current_step: str
    error: Optional[str]


# ===== 분석 에이전트 =====
ANALYZER_SYSTEM_PROMPT = """당신은 일대기 텍스트 분석 전문가입니다.

## 역할
주어진 텍스트를 분석하여 다음 정보를 추출합니다:
- 주인공의 이름
- 출생년도 (추정 가능한 경우)
- 현재 나이 (추정 가능한 경우)
- 전체 이야기 요약
- 언급된 인생 시기 감지 (유년기, 청년기, 중년기, 장년기, 노년기)
- 주요 테마 식별

## 주의사항
- 텍스트에서 명확히 확인되는 정보만 추출하세요
- 추측이 필요한 경우 "추정" 또는 "불명확"으로 표시하세요
- 한국어로 응답하세요"""


# ===== 통합 에이전트 =====
INTEGRATOR_SYSTEM_PROMPT = """당신은 자서전 통합 편집 전문가입니다.

## 역할
각 인생 시기별로 작성된 자서전 내용을 하나의 완성된 자서전으로 통합합니다.

## 작업 내용
1. 매력적인 자서전 제목 생성
2. 감동적인 프롤로그(서문) 작성 - 최소 500자
3. 각 시기별 내용을 자연스럽게 연결하며 챕터 구성
4. 의미 있는 에필로그(맺음말) 작성 - 최소 500자
5. 핵심 주제(key_themes)와 인생 교훈(life_lessons) 각 5개 이상 정리

## 작성 스타일
- 문학적이고 감동적인 문체
- 독자의 공감을 이끌어내는 서술
- 시간 순서에 따른 자연스러운 흐름

## 중요 사항
- 제공된 내용만 사용하고 새로운 사실을 지어내지 마세요
- 한국어로 작성하세요"""


def create_analyzer_chain(model_name: str = None):
    """분석 에이전트 체인 생성 - with_structured_output 사용"""
    model = model_name or MODEL
    llm = ChatOpenAI(model=model, temperature=0.3)
    structured_llm = llm.with_structured_output(AnalysisResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZER_SYSTEM_PROMPT),
        ("human", "다음 일대기 텍스트를 분석해주세요:\n\n{transcript}")
    ])
    
    chain = prompt | structured_llm
    return chain


def create_integrator_chain(model_name: str = None):
    """통합 에이전트 체인 생성 - with_structured_output 사용"""
    model = model_name or MODEL
    llm = ChatOpenAI(model=model, temperature=0.7)
    structured_llm = llm.with_structured_output(AutobiographyResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", INTEGRATOR_SYSTEM_PROMPT),
        ("human", "{integration_input}")
    ])
    
    chain = prompt | structured_llm
    return chain


# ===== LangGraph 노드 함수 =====
async def analyze_node(state: AutobiographyState) -> AutobiographyState:
    """일대기 분석 노드"""
    print("🔍 1단계: 일대기 분석 중...")
    
    try:
        analyzer = create_analyzer_chain()
        analysis = await analyzer.ainvoke({"transcript": state["transcript"]})
        print(f"   ✓ 분석 완료: {analysis.author_name}")
        
        return {
            **state,
            "analysis": analysis,
            "current_step": "chapters"
        }
    except Exception as e:
        return {**state, "error": str(e), "current_step": "error"}


async def write_chapters_node(state: AutobiographyState) -> AutobiographyState:
    """각 시기별 챕터 병렬 작성 노드"""
    print("\n✍️ 2단계: 인생 시기별 챕터 작성 중...")
    
    try:
        transcript = state["transcript"]
        
        # 모든 에이전트 생성
        childhood_agent = create_childhood_agent()
        youth_agent = create_youth_agent()
        middle_age_agent = create_middle_age_agent()
        mature_agent = create_mature_agent()
        elderly_agent = create_elderly_agent()
        
        # 병렬 실행
        results = await asyncio.gather(
            childhood_agent.ainvoke({"transcript": transcript}),
            youth_agent.ainvoke({"transcript": transcript}),
            middle_age_agent.ainvoke({"transcript": transcript}),
            mature_agent.ainvoke({"transcript": transcript}),
            elderly_agent.ainvoke({"transcript": transcript}),
            return_exceptions=True
        )
        
        # 결과 처리
        chapters = {}
        chapter_names = ["childhood", "youth", "middle_age", "mature", "elderly"]
        display_names = ["유년기", "청년기", "중년기", "장년기", "노년기"]
        
        for i, (name, display_name, result) in enumerate(zip(chapter_names, display_names, results)):
            if isinstance(result, Exception):
                print(f"   ⚠️ {display_name} 챕터 오류: {result}")
                chapters[f"{name}_chapter"] = None
            else:
                print(f"   ✓ {display_name} 챕터 완료")
                chapters[f"{name}_chapter"] = result
        
        return {
            **state,
            **chapters,
            "current_step": "integrate"
        }
    except Exception as e:
        return {**state, "error": str(e), "current_step": "error"}


async def integrate_node(state: AutobiographyState) -> AutobiographyState:
    """자서전 통합 노드"""
    print("\n📖 3단계: 자서전 통합 중...")
    
    try:
        analysis = state["analysis"]
        
        # 챕터 정보 수집
        chapters_info = []
        chapter_data = [
            ("유년기", "0-12세", state.get("childhood_chapter")),
            ("청년기", "13-29세", state.get("youth_chapter")),
            ("중년기", "30-49세", state.get("middle_age_chapter")),
            ("장년기", "50-64세", state.get("mature_chapter")),
            ("노년기", "65세 이상", state.get("elderly_chapter")),
        ]
        
        for period, age_range, chapter in chapter_data:
            if chapter and chapter.has_content:
                chapters_info.append(f"""
## {period} ({age_range})
제목: {chapter.title}
내용: {chapter.content}
주요 사건: {', '.join(chapter.key_events)}
감정: {', '.join(chapter.emotions)}
교훈: {chapter.lessons_learned or '없음'}
""")
            else:
                chapters_info.append(f"\n## {period} ({age_range})\n해당 시기에 대한 정보가 부족합니다.\n")
        
        integration_input = f"""
다음 내용을 바탕으로 완성된 자서전을 작성해주세요.

## 저자 정보
이름: {analysis.author_name}
출생년도: {analysis.birth_year or '불명'}
현재 나이: {analysis.current_age or '불명'}

## 일대기 요약
{analysis.summary}

## 감지된 인생 시기
{', '.join(analysis.detected_periods)}

## 주요 테마
{', '.join(analysis.main_themes)}

---
{''.join(chapters_info)}
---

위 내용을 하나의 완성된 자서전으로 통합해주세요.
제목, 프롤로그, 각 챕터(period, title, content를 포함한 dict), 에필로그를 포함하여 완성도 높은 자서전을 작성하세요.
"""
        
        integrator = create_integrator_chain()
        result = await integrator.ainvoke({"integration_input": integration_input})
        
        print("   ✓ 자서전 통합 완료")
        
        return {
            **state,
            "final_autobiography": result,
            "current_step": "complete"
        }
    except Exception as e:
        return {**state, "error": str(e), "current_step": "error"}


def should_continue(state: AutobiographyState) -> str:
    """다음 단계 결정"""
    if state.get("error"):
        return "error"
    return state["current_step"]


def create_orchestrator():
    """오케스트레이션 그래프 생성"""
    
    # 그래프 빌더
    builder = StateGraph(AutobiographyState)
    
    # 노드 추가
    builder.add_node("analyze", analyze_node)
    builder.add_node("write_chapters", write_chapters_node)
    builder.add_node("integrate", integrate_node)
    
    # 엣지 설정
    builder.set_entry_point("analyze")
    
    builder.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "chapters": "write_chapters",
            "error": END
        }
    )
    
    builder.add_conditional_edges(
        "write_chapters",
        should_continue,
        {
            "integrate": "integrate",
            "error": END
        }
    )
    
    builder.add_conditional_edges(
        "integrate",
        should_continue,
        {
            "complete": END,
            "error": END
        }
    )
    
    # 그래프 컴파일
    graph = builder.compile()
    
    return graph


async def run_autobiography_generation(transcript: str) -> AutobiographyResult:
    """
    자서전 생성 전체 프로세스를 실행합니다.
    
    LangGraph 기반 워크플로우를 사용하여 각 에이전트를 병렬로 실행하고 결과를 통합합니다.
    
    Args:
        transcript: 일대기 텍스트 (음성 변환 결과 또는 직접 입력)
    
    Returns:
        완성된 자서전 결과
    """
    print("📚 자서전 생성을 시작합니다...")
    
    # 초기 상태
    initial_state: AutobiographyState = {
        "transcript": transcript,
        "analysis": None,
        "childhood_chapter": None,
        "youth_chapter": None,
        "middle_age_chapter": None,
        "mature_chapter": None,
        "elderly_chapter": None,
        "final_autobiography": None,
        "current_step": "analyze",
        "error": None,
    }
    
    # 그래프 실행
    graph = create_orchestrator()
    final_state = await graph.ainvoke(initial_state)
    
    if final_state.get("error"):
        raise Exception(f"자서전 생성 중 오류 발생: {final_state['error']}")
    
    print("\n🎉 자서전 생성이 완료되었습니다!")
    
    return final_state["final_autobiography"]
