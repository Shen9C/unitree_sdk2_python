import json
import unittest
from unittest import mock

from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient as G1AudioClient


class TestG1TtsIndexIncrement(unittest.TestCase):
    """C3 回归：TtsMaker 曾执行 self.tts_index += self.tts_index，索引不递增。"""

    def test_index_increments_by_one(self):
        client = G1AudioClient.__new__(G1AudioClient)
        client.tts_index = 0

        sent_indexes = []

        def fake_call(api_id, parameter):
            sent_indexes.append(json.loads(parameter)["index"])
            return 0, ""

        with mock.patch.object(G1AudioClient, "_Call", side_effect=fake_call):
            for _ in range(3):
                self.assertEqual(client.TtsMaker("hello", 0), 0)

        self.assertEqual(sent_indexes, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
