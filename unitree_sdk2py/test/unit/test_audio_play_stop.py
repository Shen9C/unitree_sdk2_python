import unittest
from unittest import mock

from unitree_sdk2py.a2.audio.audio_client import AudioClient as A2AudioClient
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient as G1AudioClient


class TestPlayStopReturnCode(unittest.TestCase):
    """C2 回归：PlayStop 曾忽略底层返回码、恒定返回 0。"""

    CASES = (0, 3102, 3104, 3203)

    def _assert_passthrough(self, client_cls):
        # 仅测方法逻辑，绕过 Client.__init__ 的 DDS 初始化
        for expected in self.CASES:
            client = client_cls.__new__(client_cls)
            with mock.patch.object(
                client_cls, "_Call", return_value=(expected, None)
            ) as call_mock:
                self.assertEqual(client.PlayStop("demo"), expected)
            api_id, parameter = call_mock.call_args[0]
            self.assertEqual(api_id, 1004)
            self.assertEqual(parameter, '{"app_name": "demo"}')

    def test_a2_play_stop_passthrough(self):
        self._assert_passthrough(A2AudioClient)

    def test_g1_play_stop_passthrough(self):
        self._assert_passthrough(G1AudioClient)


if __name__ == "__main__":
    unittest.main()
