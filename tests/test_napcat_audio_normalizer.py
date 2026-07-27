"""NapCat 语音音频规范化的端到端回归测试。"""

import asyncio
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from core.napcat_audio_normalizer import NapCatAudioNormalizer


FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


@unittest.skipUnless(FFMPEG_AVAILABLE, "需要本机 ffmpeg 与 ffprobe")
class NapCatAudioNormalizerTests(unittest.TestCase):
    """验证高码率音频在发送前会变成体积更小、扩展名正确的 MP3。"""

    def test_normalizes_misnamed_flac_to_mono_low_bitrate_mp3(self):
        """FLAC 即使误用 .mp3 后缀，也必须输出真实的单声道 MP3。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=44100:duration=2",
                    "-ac",
                    "2",
                    "-c:a",
                    "flac",
                    "-f",
                    "flac",
                    str(source),
                ],
                check=True,
            )

            normalized = asyncio.run(
                NapCatAudioNormalizer().normalize_for_record(source)
            )
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=codec_name,channels,sample_rate,bit_rate",
                    "-of",
                    "json",
                    str(normalized),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            stream = json.loads(probe.stdout)["streams"][0]

            self.assertEqual(normalized.suffix, ".mp3")
            self.assertEqual(stream["codec_name"], "mp3")
            self.assertEqual(stream["channels"], 1)
            self.assertEqual(stream["sample_rate"], "24000")
            self.assertLess(normalized.stat().st_size, source.stat().st_size)


if __name__ == "__main__":
    unittest.main()
