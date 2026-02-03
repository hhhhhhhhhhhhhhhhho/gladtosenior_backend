"""
파일 핸들러 서비스

텍스트 파일 읽기/쓰기 및 자서전 출력을 담당합니다.
"""

import os
import json
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


class FileHandler:
    """
    파일 입출력 핸들러
    
    텍스트 입력 파일 읽기, 자서전 출력 파일 생성 등을 담당합니다.
    """
    
    SUPPORTED_TEXT_FORMATS = {'.txt', '.md', '.text'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.flac'}
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        FileHandler 초기화
        
        Args:
            output_dir: 출력 파일 저장 디렉토리 (기본값: ./output)
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_input_type(self, file_path: str) -> str:
        """
        입력 파일 타입 감지
        
        Args:
            file_path: 파일 경로
        
        Returns:
            'text' 또는 'audio'
        
        Raises:
            ValueError: 지원하지 않는 파일 형식
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in self.SUPPORTED_TEXT_FORMATS:
            return 'text'
        elif suffix in self.SUPPORTED_AUDIO_FORMATS:
            return 'audio'
        else:
            raise ValueError(
                f"지원하지 않는 파일 형식입니다: {suffix}\n"
                f"지원 텍스트 형식: {', '.join(self.SUPPORTED_TEXT_FORMATS)}\n"
                f"지원 오디오 형식: {', '.join(self.SUPPORTED_AUDIO_FORMATS)}"
            )
    
    def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        텍스트 파일 읽기
        
        Args:
            file_path: 파일 경로
            encoding: 파일 인코딩
        
        Returns:
            파일 내용
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    
    def save_autobiography(
        self,
        autobiography: Union[dict, object],
        author_name: str,
        format: str = 'all'
    ) -> dict:
        """
        자서전을 파일로 저장
        
        Args:
            autobiography: 자서전 데이터 (AutobiographyResult 또는 dict)
            author_name: 저자 이름
            format: 저장 형식 ('md', 'txt', 'json', 'all')
        
        Returns:
            저장된 파일 경로 딕셔너리
        """
        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(author_name)
        base_name = f"{safe_name}_자서전_{timestamp}"
        
        # dict로 변환
        if hasattr(autobiography, 'model_dump'):
            data = autobiography.model_dump()
        elif hasattr(autobiography, '__dict__'):
            data = autobiography.__dict__
        else:
            data = autobiography
        
        saved_files = {}
        
        # Markdown 형식
        if format in ('md', 'all'):
            md_path = self.output_dir / f"{base_name}.md"
            md_content = self._to_markdown(data)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            saved_files['markdown'] = str(md_path)
        
        # 텍스트 형식
        if format in ('txt', 'all'):
            txt_path = self.output_dir / f"{base_name}.txt"
            txt_content = self._to_plain_text(data)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            saved_files['text'] = str(txt_path)
        
        # JSON 형식
        if format in ('json', 'all'):
            json_path = self.output_dir / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            saved_files['json'] = str(json_path)
        
        return saved_files
    
    def _sanitize_filename(self, name: str) -> str:
        """파일명에 사용할 수 없는 문자 제거"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def _to_markdown(self, data: dict) -> str:
        """자서전 데이터를 Markdown으로 변환"""
        lines = []
        
        # 제목
        title = data.get('title', '나의 이야기')
        author = data.get('author_name', '저자 미상')
        lines.append(f"# {title}")
        lines.append(f"\n**저자: {author}**\n")
        lines.append("---\n")
        
        # 프롤로그
        prologue = data.get('prologue', '')
        if prologue:
            lines.append("## 프롤로그\n")
            lines.append(prologue)
            lines.append("\n---\n")
        
        # 각 챕터
        chapters = data.get('chapters', [])
        for i, chapter in enumerate(chapters, 1):
            if isinstance(chapter, dict):
                chapter_title = chapter.get('title', f'제{i}장')
                chapter_content = chapter.get('content', '')
                chapter_period = chapter.get('period', '')
                
                lines.append(f"## 제{i}장: {chapter_title}")
                if chapter_period:
                    lines.append(f"*{chapter_period}*\n")
                lines.append(chapter_content)
                lines.append("\n")
            else:
                lines.append(f"## 제{i}장\n")
                lines.append(str(chapter))
                lines.append("\n")
        
        # 에필로그
        epilogue = data.get('epilogue', '')
        if epilogue:
            lines.append("---\n")
            lines.append("## 에필로그\n")
            lines.append(epilogue)
            lines.append("\n")
        
        # 핵심 주제
        themes = data.get('key_themes', [])
        if themes:
            lines.append("---\n")
            lines.append("### 이 자서전의 핵심 주제\n")
            for theme in themes:
                lines.append(f"- {theme}")
            lines.append("\n")
        
        # 인생의 교훈
        lessons = data.get('life_lessons', [])
        if lessons:
            lines.append("### 삶의 교훈\n")
            for lesson in lessons:
                lines.append(f"- {lesson}")
            lines.append("\n")
        
        return '\n'.join(lines)
    
    def _to_plain_text(self, data: dict) -> str:
        """자서전 데이터를 일반 텍스트로 변환"""
        lines = []
        
        # 제목
        title = data.get('title', '나의 이야기')
        author = data.get('author_name', '저자 미상')
        lines.append(f"{'=' * 50}")
        lines.append(f"{title}")
        lines.append(f"저자: {author}")
        lines.append(f"{'=' * 50}\n")
        
        # 프롤로그
        prologue = data.get('prologue', '')
        if prologue:
            lines.append("[프롤로그]\n")
            lines.append(prologue)
            lines.append(f"\n{'-' * 40}\n")
        
        # 각 챕터
        chapters = data.get('chapters', [])
        for i, chapter in enumerate(chapters, 1):
            if isinstance(chapter, dict):
                chapter_title = chapter.get('title', f'제{i}장')
                chapter_content = chapter.get('content', '')
                chapter_period = chapter.get('period', '')
                
                lines.append(f"[제{i}장: {chapter_title}]")
                if chapter_period:
                    lines.append(f"({chapter_period})\n")
                lines.append(chapter_content)
            else:
                lines.append(f"[제{i}장]\n")
                lines.append(str(chapter))
            lines.append(f"\n{'-' * 40}\n")
        
        # 에필로그
        epilogue = data.get('epilogue', '')
        if epilogue:
            lines.append("[에필로그]\n")
            lines.append(epilogue)
            lines.append("\n")
        
        # 핵심 주제
        themes = data.get('key_themes', [])
        if themes:
            lines.append(f"{'=' * 50}")
            lines.append("[이 자서전의 핵심 주제]")
            for theme in themes:
                lines.append(f"  • {theme}")
            lines.append("")
        
        # 인생의 교훈
        lessons = data.get('life_lessons', [])
        if lessons:
            lines.append("[삶의 교훈]")
            for lesson in lessons:
                lines.append(f"  • {lesson}")
        
        return '\n'.join(lines)
