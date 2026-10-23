import json
import unittest
from unittest import mock

from unitree_sdk2py.h1.loco.h1_loco_client import LocoClient

GET_METHODS = [
    ("GetFsmId", 8001),
    ("GetFsmMode", 8002),
    ("GetBalanceMode", 8003),
    ("GetSwingHeight", 8004),
    ("GetStandHeight", 8005),
    ("GetPhase", 8006),
]


class TestH1LocoGetMethods(unittest.TestCase):
    """C4：h1 loco 已注册 8001–8006 GET API，此前缺公开方法。"""

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


SET_METHODS = [
    ("SetBalanceMode", 8102, 1),
    ("SetSwingHeight", 8103, 0.1),
]


class TestH1LocoSetMethods(unittest.TestCase):
    """C4：h1 loco 已注册 8102/8103 SET API，此前缺公开方法。"""

    def test_payload_and_return_code(self):
        client = LocoClient.__new__(LocoClient)
        for name, api_id, value in SET_METHODS:
            with self.subTest(method=name):
                with mock.patch.object(
                    LocoClient, "_Call", return_value=(0, "")
                ) as call_mock:
                    self.assertEqual(getattr(client, name)(value), 0)
                self.assertEqual(call_mock.call_args[0][0], api_id)
                self.assertEqual(
                    json.loads(call_mock.call_args[0][1]), {"data": value}
                )

    def test_error_code_returned(self):
        client = LocoClient.__new__(LocoClient)
        for name, _, value in SET_METHODS:
            with self.subTest(method=name):
                with mock.patch.object(
                    LocoClient, "_Call", return_value=(3104, "")
                ):
                    self.assertEqual(getattr(client, name)(value), 3104)


if __name__ == "__main__":
    unittest.main()