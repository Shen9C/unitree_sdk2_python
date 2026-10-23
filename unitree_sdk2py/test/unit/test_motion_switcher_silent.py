import json
import unittest
from unittest import mock

from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import (
    MotionSwitcherClient,
)


class TestMotionSwitcherSilent(unittest.TestCase):
    """C8：motion_switcher 注册了 1004/1005，此前缺 SetSilent/GetSilent。"""

    def test_set_silent_payload_and_return(self):
        client = MotionSwitcherClient.__new__(MotionSwitcherClient)
        for value in (True, False):
            with self.subTest(silent=value):
                with mock.patch.object(
                    MotionSwitcherClient, "_Call", return_value=(0, "")
                ) as call_mock:
                    self.assertEqual(client.SetSilent(value), (0, None))
                self.assertEqual(call_mock.call_args[0][0], 1004)
                self.assertEqual(
                    json.loads(call_mock.call_args[0][1]), {"silent": value}
                )

    def test_set_silent_error_code_propagates(self):
        client = MotionSwitcherClient.__new__(MotionSwitcherClient)
        with mock.patch.object(
            MotionSwitcherClient, "_Call", return_value=(3104, "")
        ):
            self.assertEqual(client.SetSilent(True), (3104, None))

    def test_get_silent_success_returns_parsed_json(self):
        client = MotionSwitcherClient.__new__(MotionSwitcherClient)
        with mock.patch.object(
            MotionSwitcherClient, "_Call", return_value=(0, '{"silent": true}')
        ) as call_mock:
            self.assertEqual(client.GetSilent(), (0, {"silent": True}))
        self.assertEqual(call_mock.call_args[0][0], 1005)
        self.assertEqual(call_mock.call_args[0][1], "{}")

    def test_get_silent_error_returns_none(self):
        client = MotionSwitcherClient.__new__(MotionSwitcherClient)
        with mock.patch.object(
            MotionSwitcherClient, "_Call", return_value=(3104, "")
        ):
            self.assertEqual(client.GetSilent(), (3104, None))


if __name__ == "__main__":
    unittest.main()
