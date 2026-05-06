"""
upload_paths.py

업로드 파일 저장 경로를 관리하는 모듈

역할
- 업로드 기본 디렉토리 경로 생성
- 오디오 저장 디렉토리 경로 생성
- 이미지 저장 디렉토리 경로 생성
- 폴더가 없으면 자동 생성

현재 프로젝트 기준 저장 구조 예시
-------------------------------
uploads/
├─ audio/
└─ images/
"""

from __future__ import annotations

import os

from config.settings import settings


# -----------------------------------------
# 기본 업로드 디렉토리
# -----------------------------------------
BASE_UPLOAD_DIR = settings.upload_dir

# 오디오 저장 디렉토리
AUDIO_UPLOAD_DIR = os.path.join(BASE_UPLOAD_DIR, settings.audio_dir)

# 이미지 저장 디렉토리
IMAGE_UPLOAD_DIR = os.path.join(BASE_UPLOAD_DIR, settings.image_dir)


def ensure_upload_dirs() -> None:
    """
    업로드 디렉토리가 없으면 생성

    앱 시작 시 또는 파일 저장 직전에 호출할 수 있음
    """

    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)
    os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)

