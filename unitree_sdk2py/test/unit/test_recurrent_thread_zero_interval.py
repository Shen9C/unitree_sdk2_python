import sys
import time
import types
import unittest

# utils/thread.py 模块级执行 `from .timerfd import *`，而 timerfd 依赖 Linux 的 ctypes.CDLL(None)。
# 本用例只覆盖 interval <= 0 的纯 Python 分支（不触碰 timerfd），
# 因此注入桩模块，使该回归在非 Linux 平台同样可验证。
if "unitree_sdk2py.utils.timerfd" not in sys.modules:
    _stub = types.ModuleType("unitree_sdk2py.utils.timerfd")
    _stub.timerfd_create = lambda *args: -1
    _stub.timerfd_settime = lambda *args: -1
    _stub.timerfd_gettime = lambda *args: -1
    _stub.itimerspec = None
    _stub.timespec = None
    sys.modules["unitree_sdk2py.utils.timerfd"] = _stub

from unitree_sdk2py.utils.thread import RecurrentThread


class TestRecurrentThreadNonPositiveInterval(unittest.TestCase):
    """C5 回归：interval <= 0 分支曾引用不存在的 self.__args/__kwargs，必抛 AttributeError。"""

    def test_target_is_invoked_with_args_and_kwargs(self):
        calls = []

        def target(a, b, key=None):
            calls.append((a, b, key))

        thread = RecurrentThread(
            interval=0.0, target=target, args=(1, 2), kwargs={"key": 3}
        )
        thread.Start()

        deadline = time.time() + 0.5
        while not calls and time.time() < deadline:
            time.sleep(0.005)

        thread.Wait(2.0)

        self.assertEqual(calls[:1], [(1, 2, 3)])

    def test_none_interval_uses_same_branch(self):
        calls = []

        def target():
            calls.append(1)

        thread = RecurrentThread(interval=None, target=target)
        thread.Start()

        deadline = time.time() + 0.5
        while not calls and time.time() < deadline:
            time.sleep(0.005)

        thread.Wait(2.0)

        self.assertGreaterEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
