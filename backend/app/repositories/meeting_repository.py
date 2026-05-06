"""
meeting_repository.py

Meeting 테이블에 대한 DB 접근 로직을 담당하는 Repository

역할
- 회의 생성
- 회의 단건 조회
- 회의 목록 조회
- 회의 수정
- 회의 삭제

주의
- 비즈니스 로직은 services 계층에서 처리
- 이 파일은 DB CRUD에 집중
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.meeting_model import Meeting
from schemas.meeting_schema import MeetingCreate, MeetingUpdate


def create_meeting(db: Session, meeting_data: MeetingCreate) -> Meeting:
    """
    회의 생성

    Parameters
    ----------
    db : Session
        SQLAlchemy DB 세션

    meeting_data : MeetingCreate
        회의 생성 요청 데이터
    """

    meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


def get_meeting_by_id(db: Session, meeting_id: int) -> Optional[Meeting]:
    """
    회의 ID로 단건 조회
    """

    return (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )


def get_all_meetings(db: Session, skip: int = 0, limit: int = 100) -> list[Meeting]:
    """
    회의 목록 조회

    Parameters
    ----------
    skip : int
        건너뛸 개수

    limit : int
        최대 조회 개수
    """

    return (
        db.query(Meeting)
        .order_by(Meeting.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_meeting(
    db: Session,
    meeting: Meeting,
    meeting_data: MeetingUpdate,
) -> Meeting:
    """
    회의 수정

    Parameters
    ----------
    meeting : Meeting
        수정 대상 Meeting ORM 객체

    meeting_data : MeetingUpdate
        수정할 데이터
    """

    if meeting_data.title is not None:
        meeting.title = meeting_data.title

    if meeting_data.description is not None:
        meeting.description = meeting_data.description

    db.commit()
    db.refresh(meeting)

    return meeting


def delete_meeting(db: Session, meeting: Meeting) -> None:
    """
    회의 삭제
    """

    db.delete(meeting)
    db.commit()
