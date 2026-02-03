"""
오디오 트랜스크립션 서비스

OpenAI Whisper API를 사용하여 음성 파일을 텍스트로 변환합니다.
10분 이상의 긴 오디오 파일도 청크 단위로 처리합니다.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List
from openai import AsyncOpenAI

# pydub는 optional - 없으면 기본 처리만
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub 미설치: 긴 오디오 파일 분할 기능이 제한됩니다.")


class AudioTranscriber:
    """
    음성 파일을 텍스트로 변환하는 트랜스크라이버
    
    긴 오디오 파일을 청크로 분할하여 처리하고,
    결과를 하나의 텍스트로 통합합니다.
    """
    
    # Whisper API 제한: 25MB 또는 약 10분
    MAX_CHUNK_DURATION_MS = 10 * 60 * 1000  # 10분 (밀리초)
    OVERLAP_MS = 5000  # 5초 오버랩 (문맥 유지)
    
    SUPPORTED_FORMATS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.flac'}
    
    def __init__(self, api_key: Optional[str] = None, language: str = "ko"):
        """
        AudioTranscriber 초기화
        
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
            language: 오디오 언어 (기본값: 한국어)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.language = language
    
    def _validate_file(self, file_path: str) -> Path:
        """파일 유효성 검사"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"지원하지 않는 형식입니다: {path.suffix}\n"
                f"지원 형식: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        return path
    
    async def transcribe(self, file_path: str, show_progress: bool = True) -> str:
        """
        오디오 파일을 텍스트로 변환
        
        Args:
            file_path: 오디오 파일 경로
            show_progress: 진행 상황 출력 여부
        
        Returns:
            변환된 텍스트
        """
        path = self._validate_file(file_path)
        
        if show_progress:
            print(f"🎤 오디오 파일 처리 중: {path.name}")
        
        # 파일 크기 확인 (25MB 제한)
        file_size_mb = path.stat().st_size / (1024 * 1024)
        
        if file_size_mb > 25 and PYDUB_AVAILABLE:
            # 큰 파일은 청크 분할 처리
            return await self._transcribe_large_file(path, show_progress)
        else:
            # 작은 파일은 직접 처리
            return await self._transcribe_single_file(path, show_progress)
    
    async def _transcribe_single_file(self, path: Path, show_progress: bool) -> str:
        """단일 파일 트랜스크립션"""
        if show_progress:
            print("   🔄 트랜스크립션 진행 중...")
        
        with open(path, "rb") as audio_file:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=self.language,
                response_format="text",
            )
        
        if show_progress:
            print("   ✅ 트랜스크립션 완료")
        
        return response
    
    async def _transcribe_large_file(self, path: Path, show_progress: bool) -> str:
        """큰 파일 청크 분할 트랜스크립션"""
        if not PYDUB_AVAILABLE:
            raise ImportError("pydub가 필요합니다: pip install pydub")
        
        if show_progress:
            print("   📦 큰 파일 - 청크 분할 처리 중...")
        
        # 오디오 로드
        audio = AudioSegment.from_file(str(path))
        duration_ms = len(audio)
        
        if show_progress:
            print(f"   ⏱️ 총 길이: {duration_ms / 60000:.1f}분")
        
        # 청크 분할
        chunks = self._split_audio(audio)
        
        if show_progress:
            print(f"   📦 {len(chunks)}개의 청크로 분할")
        
        # 임시 디렉토리 생성
        temp_dir = Path(path.parent) / ".temp_audio"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 청크별 트랜스크립션
            tasks = []
            for i, chunk in enumerate(chunks):
                tasks.append(self._transcribe_chunk(chunk, i, temp_dir))
            
            if show_progress:
                print("   🔄 트랜스크립션 진행 중...")
            
            results = await asyncio.gather(*tasks)
            
            if show_progress:
                print("   ✅ 트랜스크립션 완료")
            
            # 결과 통합
            return "\n\n".join(results)
            
        finally:
            # 임시 디렉토리 삭제
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _split_audio(self, audio) -> List:
        """긴 오디오를 청크로 분할"""
        duration_ms = len(audio)
        
        if duration_ms <= self.MAX_CHUNK_DURATION_MS:
            return [audio]
        
        chunks = []
        start_ms = 0
        
        while start_ms < duration_ms:
            end_ms = min(start_ms + self.MAX_CHUNK_DURATION_MS, duration_ms)
            chunk = audio[start_ms:end_ms]
            chunks.append(chunk)
            start_ms = end_ms - self.OVERLAP_MS
            
            if duration_ms - start_ms < self.OVERLAP_MS * 2:
                break
        
        return chunks
    
    async def _transcribe_chunk(self, chunk, chunk_index: int, temp_dir: Path) -> str:
        """단일 청크 트랜스크립션"""
        temp_file = temp_dir / f"chunk_{chunk_index}.mp3"
        chunk.export(str(temp_file), format="mp3")
        
        try:
            with open(temp_file, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=self.language,
                    response_format="text",
                )
            return response
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def transcribe_sync(self, file_path: str, show_progress: bool = True) -> str:
        """동기 방식 트랜스크립션 (편의 메서드)"""
        return asyncio.run(self.transcribe(file_path, show_progress))


async def transcribe_audio_file(file_path: str, language: str = "ko") -> str:
    """오디오 파일을 텍스트로 변환하는 편의 함수"""
    transcriber = AudioTranscriber(language=language)
    return await transcriber.transcribe(file_path)
