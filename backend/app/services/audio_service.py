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
- 여러 transcript를 하나의 combined_transcript로 합치기
- combined_transcript를 LLM 요약 함수에 한 번만 전달
- 최종 MeetingSummary 1개 생성

흐름
upload_router
    ↓
audio_service
    ↓
meeting_repository
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

# 중요:
# combined_transcript는 이미 문자열이므로 summarize_meeting()이 아니라
# summarize_meeting_from_text()를 사용해야 한다.
from ai.meeting_summarizer import summarize_meeting_from_text


def _process_single_audio_to_transcript(
    db: Session,
    meeting_id: int,
    upload_file: UploadFile,
) -> TranscriptResponse | None:
    """
    오디오 파일 1개를 처리해서 transcript DB에 저장한다.

    주의
    ----
    STT 결과가 빈 문자열이면 TranscriptCreate.content 검증 오류가 발생할 수 있다.
    따라서 STT 결과가 비어 있으면 DB 저장을 하지 않고 None을 반환한다.

    동작 방식
    --------
    1. 파일명 확인
    2. 오디오 파일 저장
    3. 오디오 전처리
    4. wav 변환
    5. STT 수행
    6. STT 결과가 비어 있으면 저장하지 않고 None 반환
    7. transcript DB 저장
    8. TranscriptResponse 반환
    """

    # 1. 파일명 확인
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 비어 있는 오디오 파일이 포함되어 있습니다.",
        )

    # 2. 오디오 파일 저장
    # meeting_id를 함께 넘겨 회의별 폴더에 저장되도록 처리
    saved_path = save_audio_file(
        upload_file=upload_file,
        meeting_id=meeting_id,
    )

    # 3. 오디오 전처리
    processed_path = preprocess_audio_file(saved_path)

    # 4. STT 서버 전송 전 wav 변환
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

    # 5. STT 실행
    try:
        transcript_text = transcribe_audio_file(wav_path)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STT 처리 중 오류가 발생했습니다: {str(e)}",
        )

    # 6. STT 결과 정리
    #
    # STT 서버가 {"text": ""}처럼 빈 결과를 줄 수 있다.
    # 이 상태로 TranscriptCreate(content="")를 만들면
    # content 최소 길이 검증에서 오류가 발생한다.
    transcript_text = (transcript_text or "").strip()

    if not transcript_text:
        # 빈 STT 결과는 DB에 저장하지 않고 건너뛴다.
        return None

    # 7. transcript 생성 스키마 작성
    transcript_data = TranscriptCreate(
        meeting_id=meeting_id,
        content=transcript_text,
    )

    # 8. DB 저장
    transcript = create_transcript(db, transcript_data)

    # 9. 응답 스키마 변환
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

    주의
    ----
    단일 파일 업로드에서 STT 결과가 비어 있으면
    저장할 transcript가 없으므로 400 에러를 반환한다.
    """

    # 1. 회의 존재 여부 확인
    meeting = get_meeting_by_id(db, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 meeting_id의 회의를 찾을 수 없습니다.",
        )

    # 2. 오디오 파일 1개 처리
    transcript_response = _process_single_audio_to_transcript(
        db=db,
        meeting_id=meeting_id,
        upload_file=upload_file,
    )

    # 3. STT 결과가 비어 있으면 transcript_response가 None
    if transcript_response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STT 결과가 비어 있어 transcript를 저장할 수 없습니다.",
        )

    return transcript_response


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

    # 3. 파일별 transcript 응답 저장 리스트
    transcript_responses: list[TranscriptResponse] = []

    # 4. 여러 오디오 파일을 하나씩 처리
    for upload_file in upload_files:
        transcript_response = _process_single_audio_to_transcript(
            db=db,
            meeting_id=meeting_id,
            upload_file=upload_file,
        )

        # STT 결과가 빈 파일은 None이 반환되므로 건너뛴다.
        if transcript_response is not None:
            transcript_responses.append(transcript_response)

    # 5. 저장된 transcript가 하나도 없으면 요약 생성 불가
    if not transcript_responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="모든 오디오 파일의 STT 결과가 비어 있어 회의 요약을 생성할 수 없습니다.",
        )

    # 6. transcript 내용만 추출해서 하나로 합치기
    transcript_texts: list[str] = []

    for transcript_response in transcript_responses:
        # 네 TranscriptResponse 스키마의 필드명이 content라고 가정
        content = (transcript_response.content or "").strip()

        if content:
            transcript_texts.append(content)

    combined_transcript = "\n\n".join(transcript_texts)

    # 7. 최종 combined_transcript 검증
    if not combined_transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STT 결과가 비어 있어 회의 요약을 생성할 수 없습니다.",
        )

    # 8. LLM 요약 함수 한 번만 호출
    #
    # 중요:
    # meeting_summarizer.py 기준으로 combined_transcript는 이미 문자열이므로
    # summarize_meeting()이 아니라 summarize_meeting_from_text()를 사용한다.
    #
    # 현재는 오디오만 처리하므로 ocr_text는 빈 문자열로 전달한다.
    # 나중에 OCR 결과까지 합칠 경우 ocr_text에 이미지 OCR 내용을 넣으면 된다.
    try:
        summary_result = summarize_meeting_from_text(
            stt_text=combined_transcript,
            ocr_text="",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회의 요약 생성 중 오류가 발생했습니다: {str(e)}",
        )

    # 9. SummaryCreate 생성
    #
    # summary_result 예시:
    # {
    #     "summary": "...",
    #     "decisions": [...],
    #     "action_items": [...]
    # }
    summary_data = SummaryCreate(
        meeting_id=meeting_id,
        summary=summary_result,
    )

    # 10. MeetingSummary 1개 DB 저장
    meeting_summary = create_summary(db, summary_data)

    # 11. 최종 summary 응답 반환
    return SummaryResponse.model_validate(meeting_summary)


def process_uploaded_audio_files(
    db: Session,
    meeting_id: int,
    upload_files: list[UploadFile],
) -> list[TranscriptResponse]:
    """
    여러 오디오 파일을 처리하고 transcript 목록만 반환한다.

    주의
    ----
    이 함수는 요약을 만들지 않는다.
    파일별 transcript 결과만 필요한 경우에 사용한다.

    현재 앱의 요구사항이
    '여러 오디오 파일 → transcript 저장 → combined_transcript → summary 1개 생성'
    이라면 upload_router에서는 이 함수가 아니라
    process_uploaded_audio_files_and_create_summary()를 사용해야 한다.
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

    responses: list[TranscriptResponse] = []

    # 3. 여러 오디오 파일 처리
    for upload_file in upload_files:
        transcript_response = _process_single_audio_to_transcript(
            db=db,
            meeting_id=meeting_id,
            upload_file=upload_file,
        )

        # STT 결과가 빈 파일은 저장되지 않으므로 건너뛴다.
        if transcript_response is not None:
            responses.append(transcript_response)

    # 4. 전부 빈 STT 결과라면 에러 처리
    if not responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="모든 오디오 파일의 STT 결과가 비어 있어 transcript를 저장할 수 없습니다.",
        )

    return responses