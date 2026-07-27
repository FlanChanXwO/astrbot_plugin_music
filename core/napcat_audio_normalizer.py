"""为 NapCat 语音消息准备体积可控、扩展名正确的音频文件。"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path


class NapCatAudioNormalizationError(RuntimeError):
    """FFmpeg 无法生成可供 NapCat 读取的语音文件。"""


class NapCatAudioNormalizer:
    """通过容器已有的 FFmpeg 规范化 NapCat 的本地语音来源。

    QQ/NapCat 仍会负责最终的语音封装与上传；这里的目标是避免将高码率、
    格式错配的源音频直接交给其 Worker，从而降低其峰值内存。
    """

    async def normalize_for_record(self, source: Path) -> Path:
        """生成 24 kHz 单声道、48 kbps 的真实 MP3 文件。"""
        target = source.with_name(f"{source.stem}.{uuid.uuid4().hex}.mp3")
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "24000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "48k",
            str(target),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode == 0 and target.is_file():
            return target

        target.unlink(missing_ok=True)
        detail = stderr.decode(errors="replace").strip()
        raise NapCatAudioNormalizationError(
            f"FFmpeg 语音规范化失败（退出码 {process.returncode}）：{detail}"
        )
