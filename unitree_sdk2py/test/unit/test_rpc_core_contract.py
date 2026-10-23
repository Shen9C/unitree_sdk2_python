"""rpc/internal.py 与 core/channel_name.py 的契约常量/命名测试。

这些数值与字符串是对外冻结项，测试用于防止误改。
"""

import unittest

from unitree_sdk2py.core.channel_name import (
    ChannelType,
    GetClientChannelName,
    GetServerChannelName,
)
from unitree_sdk2py.rpc import internal


class TestRpcInternalConstants(unittest.TestCase):
    def test_api_id_partition(self):
        self.assertEqual(internal.RPC_INTERNAL_API_ID_MAX, 100)
        self.assertEqual(internal.RPC_API_ID_INTERNAL_API_VERSION, 1)
        self.assertEqual(internal.RPC_API_ID_LEASE_APPLY, 101)
        self.assertEqual(internal.RPC_API_ID_LEASE_RENEWAL, 102)

    def test_lease_term_default(self):
        self.assertEqual(internal.RPC_LEASE_TERM, 1.0)

    def test_error_codes(self):
        self.assertEqual(internal.RPC_OK, 0)
        self.assertEqual(internal.RPC_ERR_UNKNOWN, 3001)
        self.assertEqual(internal.RPC_ERR_CLIENT_SEND, 3102)
        self.assertEqual(internal.RPC_ERR_CLIENT_API_NOT_REG, 3103)
        self.assertEqual(internal.RPC_ERR_CLIENT_API_TIMEOUT, 3104)
        self.assertEqual(internal.RPC_ERR_CLIENT_API_NOT_MATCH, 3105)
        self.assertEqual(internal.RPC_ERR_CLIENT_API_DATA, 3106)
        self.assertEqual(internal.RPC_ERR_CLIENT_LEASE_INVALID, 3107)
        self.assertEqual(internal.RPC_ERR_SERVER_SEND, 3201)
        self.assertEqual(internal.RPC_ERR_SERVER_INTERNAL, 3202)
        self.assertEqual(internal.RPC_ERR_SERVER_API_NOT_IMPL, 3203)
        self.assertEqual(internal.RPC_ERR_SERVER_API_PARAMETER, 3204)
        self.assertEqual(internal.RPC_ERR_SERVER_LEASE_DENIED, 3205)
        self.assertEqual(internal.RPC_ERR_SERVER_LEASE_NOT_EXIST, 3206)
        self.assertEqual(internal.RPC_ERR_SERVER_LEASE_EXIST, 3207)


class TestChannelName(unittest.TestCase):
    def test_channel_type_values(self):
        self.assertEqual(ChannelType.SEND.value, 0)
        self.assertEqual(ChannelType.RECV.value, 1)

    def test_client_channel_names(self):
        self.assertEqual(
            GetClientChannelName("sport", ChannelType.SEND),
            "rt/api/sport/request",
        )
        self.assertEqual(
            GetClientChannelName("sport", ChannelType.RECV),
            "rt/api/sport/response",
        )

    def test_server_channel_names(self):
        self.assertEqual(
            GetServerChannelName("sport", ChannelType.SEND),
            "rt/api/sport/response",
        )
        self.assertEqual(
            GetServerChannelName("sport", ChannelType.RECV),
            "rt/api/sport/request",
        )

    def test_client_and_server_are_mirrored(self):
        for service in ("sport", "loco", "motion_switcher"):
            for t in (ChannelType.SEND, ChannelType.RECV):
                self.assertNotEqual(
                    GetClientChannelName(service, t),
                    GetServerChannelName(service, t),
                )

    def test_any_value_other_than_send_maps_to_recv_side(self):
        # 现有实现用 if/else 判断，非 SEND 的任意值都落入 else 分支
        self.assertEqual(
            GetClientChannelName("sport", "unexpected"),
            "rt/api/sport/response",
        )
        self.assertEqual(
            GetServerChannelName("sport", "unexpected"),
            "rt/api/sport/request",
        )


if __name__ == "__main__":
    unittest.main()
