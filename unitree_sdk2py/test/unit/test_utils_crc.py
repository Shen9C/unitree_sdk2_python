"""utils/crc.py 的现有行为测试（CRC 基线）。

基线值取自当前实现（Windows 纯 Python 路径）；Linux ctypes 路径应与之一致。
仅描述当前行为，不改动任何业务代码。
"""

import struct
import unittest

from unitree_sdk2py.idl.default import (
    unitree_go_msg_dds__LowCmd_,
    unitree_go_msg_dds__LowState_,
    unitree_hg_msg_dds__LowCmd_,
    unitree_hg_msg_dds__LowState_,
)
from unitree_sdk2py.utils.crc import CRC


class TestCrcPython(unittest.TestCase):
    def setUp(self):
        self.crc = CRC()

    def test_empty_input_returns_initial_value(self):
        self.assertEqual(self.crc._crc_py([]), 0xFFFFFFFF)

    def test_known_vectors(self):
        # CRC-32/MPEG-2（init 0xFFFFFFFF，无最终异或）
        self.assertEqual(self.crc._crc_py([0]), 0xC704DD7B)
        self.assertEqual(self.crc._crc_py([0xFFFFFFFF]), 0)
        self.assertEqual(self.crc._crc_py([1, 2, 3]), 0x64C51784)


class TestCrcDispatch(unittest.TestCase):
    def setUp(self):
        self.crc = CRC()

    def test_default_messages_match_baseline(self):
        self.assertEqual(self.crc.Crc(unitree_go_msg_dds__LowCmd_()), 0x4B5A4880)
        self.assertEqual(self.crc.Crc(unitree_go_msg_dds__LowState_()), 0x85F11EA6)
        self.assertEqual(self.crc.Crc(unitree_hg_msg_dds__LowCmd_()), 0xFE172F9F)
        self.assertEqual(self.crc.Crc(unitree_hg_msg_dds__LowState_()), 0xD64BB04A)

    def test_is_deterministic(self):
        msg = unitree_go_msg_dds__LowCmd_()
        self.assertEqual(self.crc.Crc(msg), self.crc.Crc(msg))

    def test_unknown_idl_type_raises_type_error(self):
        class Fake:
            __idl_typename__ = "unknown.msg.dds_.Fake_"

        with self.assertRaises(TypeError):
            self.crc.Crc(Fake())

    def test_pack_sizes_are_frozen(self):
        self.assertEqual(struct.calcsize(self.crc._CRC__packFmtLowCmd), 812)
        self.assertEqual(struct.calcsize(self.crc._CRC__packFmtLowState), 1180)
        self.assertEqual(struct.calcsize(self.crc._CRC__packFmtHGLowCmd), 1004)
        self.assertEqual(struct.calcsize(self.crc._CRC__packFmtHGLowState), 2092)


if __name__ == "__main__":
    unittest.main()
