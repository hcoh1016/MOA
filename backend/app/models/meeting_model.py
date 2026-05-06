"""
meeting_model.py

회의(Meeting) 테이블 ORM 모델

역할
- 회의의 기본 정보를 저장
- transcript, summary, image의 상위 엔티티 역할

예시 저장 데이터
- 회의 제목
- 회의 설명
- 회의 생성 시각
"""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


class Meeting(Base):
    """
    회의 기본 정보를 저장하는 ORM 모델
    """

    __tablename__ = "meetings"

    # -------------------------
    # 기본 컬럼
    # -------------------------

    # 회의 고유 ID
    id = Column(Integer, primary_key=True, index=True)

    # 회의 제목
    title = Column(String(255), nullable=False)

    # 회의 설명
    description = Column(Text, nullable=True)

    # 생성 시간
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # 수정 시간
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -------------------------
    # 관계 설정
    # -------------------------

    # 하나의 회의는 여러 transcript를 가질 수 있음
    transcripts = relationship(
        "Transcript",
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 하나의 회의는 여러 summary를 가질 수 있음
    summaries = relationship(
        "Summary",
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 하나의 회의는 여러 이미지를 가질 수 있음
    images = relationship(
        "Image",
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Meeting id={self.id} title={self.title!r}>"
