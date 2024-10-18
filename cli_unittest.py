#!/usr/bin/env python3

from click.testing import CliRunner
import unittest
from unittest.mock import patch, MagicMock
from t3a_camera_snapdragon_cli import cli


class TestCameraSnapdragonCLI(unittest.TestCase):
    def test_cli(self):
        runner = CliRunner()

        result = runner.invoke(cli)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)

        filename = "test"
        result = runner.invoke(cli, ["--filename", filename])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)

        result = runner.invoke(cli, ["--flash"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)

        result = runner.invoke(cli, ["--autofocus"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)

        result = runner.invoke(cli, ["--iso", "400"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)

        # result = runner.invoke(cli, ["--exposure_time", "142"])
        # self.assertEqual(result.exit_code, 0)
        # self.assertIn("OK", result.output)

        result = runner.invoke(cli, ["--resolution", "1600x1200"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("OK", result.output)


if __name__ == "__main__":
    unittest.main()
