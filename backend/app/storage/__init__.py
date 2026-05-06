# 파일 저장/경로 관리 패키지(placeholder).
# 업로드 경로 규칙, 파일명 정책 등을 담당할 예정입니다.

from .file_manager import save_audio_file, save_image_file
from .upload_paths import (
    AUDIO_UPLOAD_DIR,
    BASE_UPLOAD_DIR,
    IMAGE_UPLOAD_DIR,
    ensure_upload_dirs,
)

__all__ = [
    "BASE_UPLOAD_DIR",
    "AUDIO_UPLOAD_DIR",
    "IMAGE_UPLOAD_DIR",
    "ensure_upload_dirs",
    "save_audio_file",
    "save_image_file",
]