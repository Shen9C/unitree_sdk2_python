import json
import unittest
from unittest import mock

from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

GET_METHODS = [
    ("GetFsmId", 7001),
    ("GetFsmMode", 7002),
    ("GetBalanceMode", 7003),
    ("GetSwingHeight", 7004),
    ("GetStandHeight", 7005),
    ("GetPhase", 7006),
]


class TestG1LocoGetMethods(unittest.TestCase):
    """C7：g1 loco 已注册 7002–7006 GET API，此前缺公开方法。"""

    def test_success_returns_parsed_value_and_api_id(self):
        client = LocoClient.__new__(LocoClient)
        for name, api_id in GET_METHODS:
            with self.subTest(method=name):
                with mock.patch.object(
                    LocoClient, "_Call", return_value=(0, '{"data": 42}')
                ) as call_mock:
                    self.assertEqual(getattr(client, name)(), (0, 42))
                self.assertEqual(call_mock.call_args[0][0], api_id)
                self.assertEqual(call_mock.call_args[0][1], "{}")

    def test_error_propagates_without_parsing(self):
        client = LocoClient.__new__(LocoClient)
        for name, _ in GET_METHODS:
            with self.subTest(method=name):
                with mock.patch.object(
                    LocoClient, "_Call", return_value=(3104, "")
                ) as call_mock:
                    self.assertEqual(getattr(client, name)(), (3104, None))
                call_mock.assert_called_once()


class TestG1LocoSetSwingHeight(unittest.TestCase):
    """C7：g1 loco 已注册 7103 SET API，此前缺 SetSwingHeight。"""

    def test_payload_and_return_code(self):
        client = LocoClient.__new__(LocoClient)
        with mock.patch.object(LocoClient, "_Call", return_value=(0, "")) as call_mock:
            self.assertEqual(client.SetSwingHeight(0.1), 0)
        self.assertEqual(call_mock.call_args[0][0], 7103)
        self.assertEqual(json.loads(call_mock.call_args[0][1]), {"data": 0.1})

    def test_error_code_returned(self):
        client = LocoClient.__new__(LocoClient)
        with mock.patch.object(LocoClient, "_Call", return_value=(3104, "")):
            self.assertEqual(client.SetSwingHeight(0.2), 3104)


if __name__ == "__main__":
    unittest.main()
