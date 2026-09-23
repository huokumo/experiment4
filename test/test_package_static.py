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
        for path in files:
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_configuration_profiles_have_all_nodes(self):
        required = {
            "lidar_cloud_relay",
            "imu_fault_injector",
            "imu_bias_corrector",
            "camera_interface_adapter",
        }
        for path in (PACKAGE / "config").glob("sensor_calibration_*.yaml"):
            with self.subTest(path=path.name):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertEqual(required, set(data))
                for node in required:
                    self.assertIn("ros__parameters", data[node])

    def test_solution_matches_experiment3_mounting_baseline(self):
        path = PACKAGE / "config" / "sensor_calibration_solution.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        lidar = data["lidar_cloud_relay"]["ros__parameters"]
        self.assertEqual([0.0, 0.0, 0.68], lidar["xyz"])
        self.assertEqual([0.0, 0.0, 0.0], lidar["rpy"])


if __name__ == "__main__":
    unittest.main()
