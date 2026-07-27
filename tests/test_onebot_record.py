"""NapCat 原始语音消息段的回归测试。"""

import asyncio
import importlib.util
import unittest
import json
from pathlib import Path

from core.onebot_record import OneBotRecord


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ASTRBOT_AVAILABLE = importlib.util.find_spec("astrbot") is not None


class OneBotRecordTests(unittest.TestCase):
    """验证插件可把音频来源原样交给 OneBot 适配器。"""

    def test_serializes_remote_url_without_base64(self):
        """URL 模式不得触发 AstrBot 的下载、转码或 Base64 编码。"""
        url = "https://music.example.test/audio.mp3"

        self.assertEqual(
            OneBotRecord(file=url).toDict(),
            {"type": "record", "data": {"file": url}},
        )

    def test_serializes_shared_local_path_without_base64(self):
        """共享路径模式必须把容器内绝对路径原样交给 NapCat。"""
        path = "/AstrBot/data/plugin_data/astrbot_plugin_music/songs/test.mp3"

        self.assertEqual(
            OneBotRecord(file=path).toDict(),
            {"type": "record", "data": {"file": path}},
        )

    @unittest.skipUnless(ASTRBOT_AVAILABLE, "需要 AstrBot 运行环境")
    def test_bypasses_aiocqhttp_base64_record_branch(self):
        """aiocqhttp 必须把插件段作为原始 OneBot record，而非 Base64。"""
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
            AiocqhttpMessageEvent,
        )

        path = "/AstrBot/data/plugin_data/astrbot_plugin_music/songs/test.mp3"
        serialized = asyncio.run(
            AiocqhttpMessageEvent._from_segment_to_dict(OneBotRecord(file=path))
        )

        self.assertEqual(serialized["type"], "record")
        self.assertEqual(serialized["data"]["file"], path)
        self.assertFalse(serialized["data"]["file"].startswith("base64://"))


class NapCatRecordConfigSchemaTests(unittest.TestCase):
    """验证 NapCat 语音来源配置可在 WebUI 中选择。"""

    def test_declares_source_options_with_legacy_default(self):
        """新配置必须保留 Base64 默认值，并显式提供 URL 与共享路径模式。"""
        schema = json.loads(
            (PLUGIN_ROOT / "_conf_schema.json").read_text(encoding="utf-8")
        )

        source = schema["napcat_record_source"]
        self.assertEqual(source["type"], "string")
        self.assertEqual(source["default"], "base64")
        self.assertEqual(source["options"], ["base64", "url", "local_file"])


if __name__ == "__main__":
    unittest.main()
