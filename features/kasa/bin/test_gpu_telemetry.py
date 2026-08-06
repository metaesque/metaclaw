import unittest
import io
import json
from unittest.mock import patch, MagicMock
import gpu_telemetry

class TestGpuTelemetry(unittest.TestCase):

    @patch('subprocess.run')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_poll_nvidia(self, mock_stdout, mock_run):
        # Mock 'which' check passing
        mock_which = MagicMock()
        mock_which.returncode = 0

        # Mock query results
        mock_query = MagicMock()
        mock_query.stdout = "0, 45, 65, 4000, 24000\n1, 99, 82, 23000, 24000"

        mock_run.side_effect = [mock_which, mock_query]

        gpu_telemetry.poll_nvidia()
        out = mock_stdout.getvalue()

        self.assertIn("gpu_telemetry,gpu_id=nvidia_0 utilization=45.0,temp_c=65.0,vram_used_mb=4000.0,vram_total_mb=24000.0", out)
        self.assertIn("gpu_telemetry,gpu_id=nvidia_1 utilization=99.0,temp_c=82.0,vram_used_mb=23000.0,vram_total_mb=24000.0", out)

    @patch('subprocess.run')
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('os.cpu_count', return_value=8)
    def test_poll_nvidia_unified_memory(self, mock_cpu, mock_stdout, mock_run):
        mock_which = MagicMock()
        mock_which.returncode = 0
        mock_query = MagicMock()
        mock_query.stdout = "0, [N/A], 65, [N/A], [N/A]\n"
        mock_run.side_effect = [mock_which, mock_query]

        file_data = {
            "/hostfs/proc/meminfo": "MemTotal: 131072000 kB\nMemAvailable: 31072000 kB\n",
            "/hostfs/proc/loadavg": "4.00 3.00 2.00 1/100 1234\n"
        }
        def custom_open(filename, *args, **kwargs):
            if filename in file_data:
                from unittest.mock import mock_open
                return mock_open(read_data=file_data[filename])()
            raise FileNotFoundError(filename)

        with patch('builtins.open', side_effect=custom_open):
            gpu_telemetry.poll_nvidia()

        out = mock_stdout.getvalue()
        # Total MB = 131072000 / 1024 = 128000.0
        # Used MB = (131072000 - 31072000) / 1024 = 97656.25 -> 97656.2
        # CPU util = (4.0 / 8) * 100 = 50.0
        self.assertIn("gpu_telemetry,gpu_id=nvidia_0 utilization=50.0,temp_c=65.0,vram_used_mb=97656.2,vram_total_mb=128000.0", out)

    @patch('os.path.exists')
    @patch('glob.glob')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_poll_amd_sysfs(self, mock_stdout, mock_glob, mock_exists):
        mock_glob.side_effect = [
            ["/hostfs/sys/class/drm/card0"],
            ["/hostfs/sys/class/drm/card0/device/hwmon/hwmon0"]
        ]
        mock_exists.return_value = True

        from unittest.mock import mock_open
        file_data = {
            "/hostfs/sys/class/drm/card0/device/gpu_busy_percent": "100\n",
            "/hostfs/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input": "70000\n",
            "/hostfs/sys/class/drm/card0/device/mem_info_vram_used": "1048576000\n",
            "/hostfs/sys/class/drm/card0/device/mem_info_vram_total": "2516582400\n"
        }

        def custom_open(filename, *args, **kwargs):
            if filename in file_data:
                return mock_open(read_data=file_data[filename])()
            raise FileNotFoundError(filename)

        with patch('builtins.open', side_effect=custom_open):
            gpu_telemetry.poll_amd_sysfs()

        out = mock_stdout.getvalue()
        self.assertIn("gpu_telemetry,gpu_id=amd_0 utilization=100.0,temp_c=70.0,vram_used_mb=1000.0,vram_total_mb=2400.0", out)

if __name__ == '__main__':
    unittest.main()
