import unittest
from unittest import mock

from unitree_sdk2py.core.channel import Channel

Writer = Channel._Channel__Writer


class TestChannelWriterExceptionFallback(unittest.TestCase):
    """C6 回归：Channel.__Writer.Write 的兜底分支曾调用 e.args()，异常路径本身抛 TypeError。"""

    def _make_writer(self):
        writer = Writer.__new__(Writer)
        writer._Writer__writer = mock.Mock()
        writer._Writer__publication_matched_count = 0
        return writer

    def test_generic_exception_returns_false_instead_of_raising(self):
        writer = self._make_writer()
        writer._Writer__writer.write.side_effect = RuntimeError("boom")

        with mock.patch("builtins.print") as print_mock:
            self.assertFalse(writer.Write(object()))

        printed = " ".join(str(arg) for call in print_mock.call_args_list for arg in call[0])
        self.assertIn("boom", printed)

    def test_normal_write_returns_true(self):
        writer = self._make_writer()

        self.assertTrue(writer.Write(object()))
        writer._Writer__writer.write.assert_called_once()


if __name__ == "__main__":
    unittest.main()
