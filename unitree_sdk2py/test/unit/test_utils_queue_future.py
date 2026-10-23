"""utils/bqueue.py、utils/future.py、rpc/request_future.py 的现有行为测试。

仅描述当前实现的行为，不改动任何业务代码。
"""

import unittest

from unitree_sdk2py.utils.bqueue import BQueue
from unitree_sdk2py.utils.future import Future, FutureState, FutureResult
from unitree_sdk2py.rpc.request_future import RequestFuture, RequestFutureQueue


class TestBQueue(unittest.TestCase):
    def test_put_get_fifo_and_size(self):
        q = BQueue(maxLen=3)
        self.assertEqual(q.Size(), 0)
        self.assertTrue(q.Put("a"))
        self.assertTrue(q.Put("b"))
        self.assertEqual(q.Size(), 2)
        self.assertEqual(q.Get(timeout=0), "a")
        self.assertEqual(q.Get(timeout=0), "b")
        self.assertEqual(q.Size(), 0)

    def test_full_without_replace_drops_new_item(self):
        q = BQueue(maxLen=2)
        q.Put(1)
        q.Put(2)
        self.assertFalse(q.Put(3))
        self.assertEqual(q.Size(), 2)
        self.assertEqual(q.Get(timeout=0), 1)
        self.assertEqual(q.Get(timeout=0), 2)

    def test_full_with_replace_drops_oldest(self):
        q = BQueue(maxLen=2)
        q.Put(1)
        q.Put(2)
        self.assertFalse(q.Put(3, replace=True))
        self.assertEqual(q.Size(), 2)
        self.assertEqual(q.Get(timeout=0), 2)
        self.assertEqual(q.Get(timeout=0), 3)

    def test_get_empty_returns_none(self):
        q = BQueue(maxLen=2)
        self.assertIsNone(q.Get(timeout=0.01))

    def test_clear(self):
        q = BQueue(maxLen=2)
        q.Put(1)
        q.Clear()
        self.assertEqual(q.Size(), 0)
        self.assertIsNone(q.Get(timeout=0))


class TestFuture(unittest.TestCase):
    def test_ready_then_get_result_success(self):
        f = Future()
        self.assertTrue(f.Ready({"v": 1}))
        result = f.GetResult(timeout=0.01)
        self.assertEqual(result.code, FutureResult.FUTURE_SUCC)
        self.assertEqual(result.msg, "success")
        self.assertEqual(result.value, {"v": 1})

    def test_fail_then_get_result_failed(self):
        f = Future()
        self.assertTrue(f.Fail("boom"))
        result = f.GetResult(timeout=0.01)
        self.assertEqual(result.code, FutureResult.FUTURE_ERR_FAILED)
        self.assertEqual(result.msg, "boom")

    def test_get_result_timeout(self):
        f = Future()
        result = f.GetResult(timeout=0.01)
        self.assertEqual(result.code, FutureResult.FUTUTE_ERR_TIMEOUT)
        self.assertEqual(result.msg, "future wait timeout")

    def test_second_completion_is_rejected(self):
        f = Future()
        self.assertTrue(f.Ready(1))
        self.assertFalse(f.Ready(2))
        self.assertFalse(f.Fail("late"))
        self.assertEqual(f.GetResult(timeout=0).value, 1)

    def test_wait_returns_true_when_already_settled(self):
        f = Future()
        f.Ready(1)
        self.assertTrue(f.Wait(timeout=0.01))

    def test_wait_returns_false_on_timeout(self):
        f = Future()
        self.assertFalse(f.Wait(timeout=0.01))

    def test_default_state_is_defer(self):
        f = Future()
        self.assertEqual(f._Future__state, FutureState.DEFER)

    def test_future_result_str(self):
        result = FutureResult(0, "ok", 7)
        self.assertEqual(str(result), "FutureResult(code=0, msg='ok', value=7)")


class TestRequestFutureQueue(unittest.TestCase):
    def test_set_and_get_pops_entry(self):
        q = RequestFutureQueue()
        f = RequestFuture()
        self.assertTrue(q.Set(101, f))
        self.assertIs(q.Get(101), f)
        self.assertIsNone(q.Get(101))

    def test_set_none_is_rejected(self):
        q = RequestFutureQueue()
        self.assertFalse(q.Set(1, None))

    def test_remove(self):
        q = RequestFutureQueue()
        f = RequestFuture()
        q.Set(1, f)
        q.Remove(1)
        self.assertIsNone(q.Get(1))

    def test_remove_missing_id_is_noop(self):
        q = RequestFutureQueue()
        q.Remove(999)
        self.assertIsNone(q.Get(999))

    def test_request_id_roundtrip(self):
        f = RequestFuture()
        self.assertIsNone(f.GetRequestId())
        f.SetRequestId(123456)
        self.assertEqual(f.GetRequestId(), 123456)


if __name__ == "__main__":
    unittest.main()
