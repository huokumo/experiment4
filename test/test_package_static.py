import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


PACKAGE = Path(__file__).resolve().parents[1]


class PackageStaticTest(unittest.TestCase):
    def test_xml_files_are_well_formed(self):
        files = [PACKAGE / "package.xml"]
        files.extend((PACKAGE / "urdf").glob("*.xacro"))
        files.extend((PACKAGE / "worlds").glob("*.world"))
        for path in files:
            with self.subTest(path=path.name):
                ET.parse(path)

    def test_python_files_parse(self):
        files = list((PACKAGE / "launch").glob("*.py"))
        files.extend((PACKAGE / "scripts").glob("*.py"))
        files.extend((PACKAGE / "experiment4").rglob("*.py"))
        files.append(PACKAGE / "setup.py")
        for path in files:
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_working_configuration_has_all_nodes(self):
        required = {
            "lidar_cloud_relay",
            "imu_fault_injector",
            "imu_bias_corrector",
            "camera_interface_adapter",
        }
        path = PACKAGE / "config" / "sensor_calibration.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(required, set(data))
        for node in required:
            self.assertIn("ros__parameters", data[node])

    def test_initial_configuration_contains_the_three_tasks(self):
        path = PACKAGE / "config" / "sensor_calibration.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        lidar = data["lidar_cloud_relay"]["ros__parameters"]
        corrector = data["imu_bias_corrector"]["ros__parameters"]
        camera = data["camera_interface_adapter"]["ros__parameters"]
        self.assertEqual([0.05, 0.0, 0.73], lidar["xyz"])
        self.assertEqual([0.0, 0.0, 0.12], lidar["rpy"])
        self.assertEqual([0.0, 0.0, 0.0], corrector["angular_velocity_bias"])
        self.assertEqual("/wrong/image", camera["image_input"])

    def test_single_launch_and_python_console_entry_points(self):
        launches = list((PACKAGE / "launch").glob("*.launch.py"))
        self.assertEqual(["calibration.launch.py"], [path.name for path in launches])
        setup = (PACKAGE / "setup.py").read_text(encoding="utf-8")
        self.assertIn("console_scripts", setup)
        self.assertIn("lidar_cloud_relay = experiment4.entrypoints:lidar_cloud_relay", setup)


if __name__ == "__main__":
    unittest.main()
