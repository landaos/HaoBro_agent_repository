"""
file_storage.py — 文件存储服务

支持本地存储，文件按日期分目录存放。
"""
from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from src.logger.logger import logger


class FileInfo:
    """文件存储信息"""

    def __init__(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        checksum: str,
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type
        self.checksum = checksum


# 支持的文件类型
SUPPORTED_FILE_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".md": "text/markdown",
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


class FileStorageService:
    """文件存储服务（本地存储）"""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _date_subdir(self) -> str:
        """按日期生成子目录: uploads/2026/07/23/"""
        now = datetime.now()
        return now.strftime("%Y/%m/%d")

    def _generate_path(self, original_name: str) -> tuple[Path, str]:
        """生成唯一存储路径"""
        subdir = self._date_subdir()
        target_dir = self.upload_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        # 保留原始扩展名，加 uuid 前缀防冲突
        ext = Path(original_name).suffix
        unique_name = f"{uuid.uuid4().hex[:12]}_{original_name}"
        full_path = target_dir / unique_name

        return full_path, f"{subdir}/{unique_name}"

    def save(self, file_data: bytes, file_name: str) -> FileInfo:
        """
        保存文件到本地存储。

        参数:
            file_data: 文件二进制内容
            file_name: 原始文件名

        返回:
            FileInfo: 文件信息
        """
        full_path, relative_path = self._generate_path(file_name)

        # 计算 checksum
        checksum = hashlib.sha256(file_data).hexdigest()

        # 写入文件
        full_path.write_bytes(file_data)

        ext = Path(file_name).suffix.lower()
        mime = SUPPORTED_FILE_TYPES.get(ext, "application/octet-stream")

        logger.info(f"文件已保存: {relative_path} ({len(file_data):,} bytes)")
        return FileInfo(
            file_path=relative_path,
            file_name=file_name,
            file_size=len(file_data),
            mime_type=mime,
            checksum=checksum,
        )

    def read(self, file_path: str) -> bytes:
        """读取文件内容"""
        full_path = self.upload_dir / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {full_path}")
        return full_path.read_bytes()

    def delete(self, file_path: str) -> bool:
        """删除文件"""
        full_path = self.upload_dir / file_path
        if full_path.exists():
            full_path.unlink()
            logger.info(f"【文件存储】文件已删除 | {file_path}")
            return True
        return False

    def get_absolute_path(self, file_path: str) -> str:
        """获取文件绝对路径"""
        return str((self.upload_dir / file_path).resolve())

    @staticmethod
    def validate_file_type(file_name: str) -> str | None:
        """校验文件类型是否支持，返回小写扩展名"""
        ext = Path(file_name).suffix.lower()
        if ext in SUPPORTED_FILE_TYPES:
            return ext.lstrip(".")
        return None

    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, str]:
        """校验文件大小"""
        if file_size > MAX_FILE_SIZE:
            return False, f"文件大小超过限制 ({file_size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
        if file_size == 0:
            return False, "文件为空"
        return True, ""
