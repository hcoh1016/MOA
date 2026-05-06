"""
summary_repository.py

Summary 테이블에 대한 DB 접근 로직을 담당하는 Repository

역할
- summary 생성
- 회의 ID로 summary 조회
- summary 삭제

가정
- 현재 프로젝트에서는 회의당 summary를 1개로 관리
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.summary_model import Summary
from schemas.summary_schema import SummaryCreate


def create_summary(db: Session, summary_data: SummaryCreate) -> Summary:
    """
    summary 생성

    Parameters
    ----------
    db : Session
        SQLAlchemy DB 세션

    summary_data : SummaryCreate
        생성할 summary 데이터
    """

    summary = Summary(
        meeting_id=summary_data.meeting_id,
        content=summary_data.content,
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return summary


def get_summary_by_meeting_id(db: Session, meeting_id: int) -> Optional[Summary]:
    """
    특정 회의의 summary 조회

    Parameters
    ----------
    db : Session
        SQLAlchemy DB 세션

    meeting_id : int
        회의 ID

    Returns
    -------
    Optional[Summary]
        summary가 없으면 None 반환
    """

    return (
        db.query(Summary)
        .filter(Summary.meeting_id == meeting_id)
        .first()
    )


def delete_summary(db: Session, summary: Summary) -> None:
    """
    summary 삭제

    Parameters
    ----------
    db : Session
        SQLAlchemy DB 세션

    summary : Summary
        삭제할 Summary ORM 객체
    """

    db.delete(summary)
    db.commit()