# AI 모듈 패키지(placeholder).
# STT/문서 OCR/회의 요약 등 멀티모달 처리 계층을 포함합니다.

from .image_ocr import process_image_by_type
from .meeting_summarizer import summarize_meeting, summarize_meeting_from_text
from .stt_client import request_stt

__all__ = [
    "request_stt",
    "summarize_meeting",
    "summarize_meeting_from_text",
    "process_image_by_type",
]