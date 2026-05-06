"""
audio_service.py

오디오 처리 서비스 계층

역할
- 업로드된 오디오 파일 저장
- 오디오 전처리
- STT 서버 전송 전 wav 변환
- STT 수행
- transcript DB 저장
- 여러 오디오 파일 처리
- 여러 STT 결과를 하나로 합쳐 LLM 요약 1회 수행
- MeetingSummary 1개 저장

흐름
upload_router
    ↓
audio_service
    ↓
file_manager
    ↓
preprocess
    ↓
audio_converter
    ↓
stt_service
    ↓
transcript_repository
    ↓
meeting_summarizer
    ↓
summary_repository
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from repositories.meeting_repository import get_meeting_by_id
from repositories.transcript_repository import create_transcript
from repositories.summary_repository import create_summary

from schemas.transcript_schema import TranscriptCreate, TranscriptResponse
from schemas.summary_schema import SummaryCreate, SummaryResponse

from services.stt_service import transcribe_audio_file
from storage.file_manager import save_audio_file
from utils.preprocess import preprocess_audio_file
from utils.audio_converter import convert_audio_to_wav

from ai.meeting_summarizer import summarize_meeting


def _process_single_audio_to_transcript(
    db: Session,
    meeting_id: int,
    upload_file: UploadFile,
) -> TranscriptResponse:
    """
    오디오 파일 1개를 처리해서 transcript DB에 저장한다.

    이 함수는 내부 재사용용 함수이다.

    동작 방식
    --------
    1. 파일명 확인
    2. 오디오 파일 저장
    3. 오디오 전처리
    4. wav 변환
    5. STT 수행
    6. transcript DB 저장
    7. TranscriptResponse 반환
    """

    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 비어 있는 오디오 파일이 포함되어 있습니다.",
        )

    # 1. 오디오 파일 저장
    saved_path = save_audio_file(
        upload_file=upload_file,
        meeting_id=meeting_id,
    )

    # 2. 오디오 전처리
    processed_path = preprocess_audio_file(saved_path)

    # 3. STT 서버 전송 전 wav 변환
    try:
        wav_path = convert_audio_to_wav(processed_path)

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오 파일을 찾을 수 없습니다: {str(e)}",
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오디오 wav 변환 중 오류가 발생했습니다: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알 수 없는 오디오 변환 오류가 발생했습니다: {str(e)}",
        )

    # 4. STT 실행
    try:
        transcript_text = transcribe_audio_file(wav_path)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STT 처리 중 오류가 발생했습니다: {str(e)}",
        )

    # STT 결과가 None이면 빈 문자열로 처리
    if transcript_text is None:
        transcript_text = ""

    # 5. transcript 생성 스키마 작성
    transcript_data = TranscriptCreate(
        meeting_id=meeting_id,
        content=transcript_text,
    )

    # 6. transcript DB 저장
    transcript = create_transcript(db, transcript_data)

    # 7. 응답 스키마 변환
    return TranscriptResponse.model_validate(transcript)


def process_uploaded_audio(
    db: Session,
    meeting_id: int,
    upload_file: UploadFile,
) -> TranscriptResponse:
    """
    오디오 파일 1개 업로드 처리 함수.

    기존 단일 파일 업로드 API가 필요할 수 있으므로 유지한다.

    동작 방식
    --------
    1. meeting_id에 해당하는 회의 존재 여부 확인
    2. 오디오 파일 1개 처리
    3. transcript DB 저장
    4. TranscriptResponse 반환
    """

    meeting = get_meeting_by_id(db, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 meeting_id의 회의를 찾을 수 없습니다.",
        )

    return _process_single_audio_to_transcript(
        db=db,
        meeting_id=meeting_id,
        upload_file=upload_file,
    )


def process_uploaded_audio_files_and_create_summary(
    db: Session,
    meeting_id: int,
    upload_files: list[UploadFile],
) -> SummaryResponse:
    """
    여러 오디오 파일을 처리한 뒤 최종 MeetingSummary 1개를 생성한다.

    요구사항
    --------
    - files: list[UploadFile] = File(...) 로 여러 오디오 파일 받기
    - 각 파일 저장
    - 각 파일에 대해 STT 수행
    - 파일별 transcript 생성
    - 모든 transcript를 하나의 combined_transcript로 합치기
    - combined_transcript를 LLM 요약 함수에 한 번만 전달
    - 최종 summary는 MeetingSummary 1개만 생성

    Returns
    -------
    SummaryResponse
        최종 회의 요약 응답
    """

    # 1. 파일 목록 확인
    if not upload_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드된 오디오 파일이 없습니다.",
        )

    # 2. 회의 존재 여부 확인
    meeting = get_meeting_by_id(db, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 meeting_id의 회의를 찾을 수 없습니다.",
        )

    # 3. 파일별 transcript 응답 저장
    transcript_responses: list[TranscriptResponse] = []

    # 4. 여러 오디오 파일을 하나씩 처리
    for upload_file in upload_files:
        transcript_response = _process_single_audio_to_transcript(
            db=db,
            meeting_id=meeting_id,
            upload_file=upload_file,
        )

        transcript_responses.append(transcript_response)

    # 5. transcript 내용만 추출해서 하나로 합치기
    #
    # TranscriptResponse 안의 필드명이 content라고 가정한다.
    # 만약 네 schema에서 transcript라는 이름을 쓰고 있다면
    # transcript_response.content 부분을 transcript_response.transcript로 바꾸면 된다.
    transcript_texts: list[str] = []

    for transcript_response in transcript_responses:
        content = transcript_response.content

        if content and content.strip():
            transcript_texts.append(content.strip())

    combined_transcript = "\n\n".join(transcript_texts)

    # 6. STT 결과가 모두 비어 있으면 요약 생성 불가
    if not combined_transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STT 결과가 비어 있어 회의 요약을 생성할 수 없습니다.",
        )

    # 7. LLM 요약 함수는 한 번만 호출
    #
    # 현재는 오디오만 처리하므로 ocr_text는 빈 문자열로 넘긴다.
    # 나중에 이미지 OCR까지 합칠 경우 ocr_text에 OCR 내용을 넣으면 된다.
    summary_result = summarize_meeting(
        stt_text=combined_transcript,
        ocr_text="",
    )

    # 8. MeetingSummary 저장 데이터 생성
    #
    # summary_result가 dict라고 가정한다.
    # 예:
    # {
    #     "summary": "...",
    #     "decisions": [...],
    #     "action_items": [...]
    # }
    summary_data = SummaryCreate(
        meeting_id=meeting_id,
        summary=summary_result,
    )

    # 9. MeetingSummary 1개 DB 저장
    meeting_summary = create_summary(db, summary_data)

    # 10. 최종 summary 응답 반환
    return SummaryResponse.model_validate(meeting_summary)