"""
자서전 생성 프로그램 메인 모듈 (LangChain/LangGraph 기반)

Deep Agent 기반으로 일대기를 자서전으로 변환합니다.

사용법:
    # 텍스트 파일 입력
    python main.py --input story.txt
    
    # 음성 파일 입력
    python main.py --input interview.mp3
    
    # 직접 텍스트 입력
    python main.py --text "나의 이야기..."
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 환경 변수 로드
load_dotenv()

from autobiography_agents import run_autobiography_generation, AutobiographyResult
from services import AudioTranscriber, FileHandler


class AutobiographyGenerator:
    """
    자서전 생성기 메인 클래스
    
    텍스트 또는 음성 입력을 받아 완성된 자서전을 생성합니다.
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        AutobiographyGenerator 초기화
        
        Args:
            output_dir: 출력 파일 저장 디렉토리
        """
        self.file_handler = FileHandler(output_dir)
        self.audio_transcriber = None  # 필요시 초기화
    
    async def generate_from_file(self, file_path: str) -> dict:
        """
        파일에서 자서전 생성
        
        Args:
            file_path: 입력 파일 경로 (텍스트 또는 음성)
        
        Returns:
            생성 결과 딕셔너리
        """
        # 파일 타입 감지
        input_type = self.file_handler.detect_input_type(file_path)
        
        print(f"\n📁 입력 파일: {file_path}")
        print(f"📌 파일 타입: {input_type}")
        
        # 텍스트 추출
        if input_type == 'text':
            transcript = self.file_handler.read_text_file(file_path)
            print(f"📝 텍스트 길이: {len(transcript)} 자")
        else:  # audio
            if self.audio_transcriber is None:
                self.audio_transcriber = AudioTranscriber()
            transcript = await self.audio_transcriber.transcribe(file_path)
            print(f"📝 변환된 텍스트 길이: {len(transcript)} 자")
        
        # 자서전 생성
        return await self._generate(transcript)
    
    async def generate_from_text(self, text: str) -> dict:
        """
        직접 입력된 텍스트에서 자서전 생성
        
        Args:
            text: 일대기 텍스트
        
        Returns:
            생성 결과 딕셔너리
        """
        print(f"\n📝 텍스트 길이: {len(text)} 자")
        return await self._generate(text)
    
    async def _generate(self, transcript: str) -> dict:
        """
        자서전 생성 내부 로직
        
        Args:
            transcript: 일대기 텍스트
        
        Returns:
            생성 결과 딕셔너리
        """
        print("\n" + "=" * 50)
        print("⚡ LangGraph 기반 멀티 에이전트 오케스트레이션")
        
        result = await run_autobiography_generation(transcript)
        
        print("=" * 50)
        
        # 결과 저장
        if hasattr(result, 'author_name'):
            author_name = result.author_name
        elif isinstance(result, dict) and 'author_name' in result:
            author_name = result['author_name']
        else:
            author_name = "저자미상"
        
        print(f"\n💾 자서전 저장 중...")
        saved_files = self.file_handler.save_autobiography(result, author_name)
        
        print(f"\n✨ 저장 완료!")
        for format_name, path in saved_files.items():
            print(f"   📄 {format_name}: {path}")
        
        return {
            'autobiography': result,
            'saved_files': saved_files
        }


def parse_arguments():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Deep Agent 기반 자서전 생성 프로그램 (LangChain/LangGraph)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --input story.txt
  python main.py --input interview.mp3
  python main.py --text "1950년 서울에서 태어났습니다..."
        """
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input', '-i',
        type=str,
        help='입력 파일 경로 (텍스트 또는 음성 파일)'
    )
    input_group.add_argument(
        '--text', '-t',
        type=str,
        help='직접 입력할 일대기 텍스트'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./output',
        help='출력 디렉토리 (기본값: ./output)'
    )
    
    return parser.parse_args()


async def main():
    """메인 함수"""
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 오류: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하거나 환경 변수를 설정해주세요.")
        sys.exit(1)
    
    args = parse_arguments()
    
    print("\n" + "=" * 50)
    print("📚 Deep Agent 자서전 생성기")
    print("   (LangChain + LangGraph 기반)")
    print("=" * 50)
    
    generator = AutobiographyGenerator(output_dir=args.output)
    
    try:
        if args.input:
            result = await generator.generate_from_file(args.input)
        else:
            result = await generator.generate_from_text(args.text)
        
        print("\n" + "=" * 50)
        print("🎉 자서전 생성 완료!")
        print("=" * 50)
        
    except FileNotFoundError as e:
        print(f"\n❌ 파일 오류: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ 입력 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
