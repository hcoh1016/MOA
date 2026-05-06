"""
meeting_schema.py

회의(Meeting) 관련 요청/응답 스키마 정의

역할
- 회의 생성 요청 검증
- 회의 응답 형식 정의
- FastAPI에서 request/response 모델로 사용

주의
- DB 테이블 구조는 models/meeting_model.py에서 관리
- 이 파일은 API 입력/출력 형식만 다룸
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MeetingCreate(BaseModel):
    """
    회의 생성 요청 스키마

    사용 예
    -------
    POST /meetings
    {
        "title": "AI 회의록 프로젝트 회의",
        "description": "DB 구조 및 API 설계 논의"
    }
    """

    title: str = Field(..., min_length=1, max_length=255, description="회의 제목")
    description: Optional[str] = Field(
        default=None,
        description="회의 설명"
    )


class MeetingUpdate(BaseModel):
    """
    회의 수정 요청 스키마

    부분 수정이 가능하도록 모든 필드를 optional로 둠
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="수정할 회의 제목"
    )
    description: Optional[str] = Field(
        default=None,
        description="수정할 회의 설명"
    )


class MeetingResponse(BaseModel):
    """
    회의 응답 스키마

    DB에서 조회한 Meeting ORM 객체를 API 응답으로 변환할 때 사용
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime