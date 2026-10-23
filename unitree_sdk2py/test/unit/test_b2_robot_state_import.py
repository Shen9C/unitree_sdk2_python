import importlib
import unittest


class TestB2RobotStateImport(unittest.TestCase):
    """C1 回归：b2/robot_state 曾误写 rpc.client_internal，导致导入即 ModuleNotFoundError。"""

    def test_module_importable(self):
        module = importlib.import_module(
            "unitree_sdk2py.b2.robot_state.robot_state_client"
        )
        self.assertTrue(hasattr(module, "RobotStateClient"))
        self.assertTrue(hasattr(module, "ServiceState"))

    def test_api_constants_reachable(self):
        from unitree_sdk2py.b2.robot_state.robot_state_client import RobotStateClient
        from unitree_sdk2py.b2.robot_state import robot_state_api
        from unitree_sdk2py.rpc.client import Client

        self.assertEqual(robot_state_api.ROBOT_STATE_SERVICE_NAME, "robot_state")
        self.assertEqual(robot_state_api.ROBOT_STATE_API_VERSION, "1.0.0.2")
        self.assertEqual(robot_state_api.ROBOT_STATE_API_ID_SERVICE_SWITCH, 1001)
        self.assertEqual(robot_state_api.ROBOT_STATE_API_ID_GET_PKG_VERSION, 1006)
        self.assertEqual(robot_state_api.ROBOT_STATE_ERR_SERVICE_SWITCH, 5201)
        self.assertEqual(robot_state_api.ROBOT_STATE_ERR_SERVICE_PROTECTED, 5202)
        self.assertTrue(issubclass(RobotStateClient, Client))


if __name__ == "__main__":
    unittest.main()
