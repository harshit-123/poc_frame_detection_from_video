import os
import shutil

from fastapi import UploadFile


def ensure_directories(*paths: str) -> None:
    for path in paths:
        os.makedirs(path, exist_ok=True)


def save_upload_file(upload_file: UploadFile, path: str) -> None:
    upload_file.file.seek(0)
    with open(path, "wb") as output_file:
        shutil.copyfileobj(upload_file.file, output_file)
