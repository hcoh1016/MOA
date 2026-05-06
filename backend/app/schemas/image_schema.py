"""
image_schema.py

이미지(Image) 관련 요청/응답 스키마 정의

역할
- 이미지 업로드 결과 응답 형식 정의
- OCR 결과 / 분석 결과 응답 형식 정의
- 일반 이미지와 화이트보드 이미지를 image_type으로 구분

image_type 예시
---------------
- image
- whiteboard
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


ImageType = Literal["image", "whiteboard"]


class ImageCreate(BaseModel):
    """
    이미지 생성 요청 스키마

    주로 내부 테스트나 수동 생성에 사용 가능
    """

    meeting_id: int = Field(..., gt=0, description="회의 ID")
    file_path: str = Field(..., min_length=1, description="저장된 파일 경로")
    image_type: ImageType = Field(default="image", description="이미지 종류")
    ocr_text: Optional[str] = Field(default=None, description="OCR 추출 텍스트")
    analysis_text: Optional[str] = Field(default=None, description="이미지 분석 결과")


class ImageResponse(BaseModel):
    """
    이미지 응답 스키마
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    file_path: str
    image_type: ImageType
    ocr_text: Optional[str] = None
    analysis_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ImageUploadResponse(BaseModel):
    """
    이미지 업로드 API 응답 스키마

    업로드 직후 OCR/분석 결과를 함께 반환할 때 사용
    """

    meeting_id: int
    file_path: str
    image_type: ImageType
    ocr_text: Optional[str] = None
    analysis_text: Optional[str] = None