import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Inject the lib directory directly to support local module imports (e.g., 'import devices')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
from metaclaw import Error, MetaClaw, Markdown

class TestError(unittest.TestCase):
    def test___init__(self):
        err = Error("test error")
        self.assertEqual(str(err), "test error")

class TestMetaClaw(unittest.TestCase):
    def setUp(self):
        self.mc = MetaClaw()

    def test___init__(self):
        self.assertIsNone(self.mc._structure)
        self.assertEqual(self.mc._timestamp, 0)
        self.assertIsNone(self.mc._hardware)
        self.assertIsNone(self.mc._devices)

    @patch('devices.get_all_devices')
    def test_devices(self, mock_get_all_devices):
        mock_get_all_devices.return_value = {"test": "device"}
        devs = self.mc.devices()
        self.assertEqual(devs, {"test": "device"})
        mock_get_all_devices.assert_called_once()

    @patch.object(MetaClaw, 'structure')
    def test_subpath(self, mock_structure):
        mock_structure.return_value = {
            "services": {"proxy": {"uids": "proxies"}}
        }
        path = self.mc.subpath(service="proxy", provider="litellm", base="config.yaml")
        self.assertTrue(path.endswith(os.path.join("services", "proxies", "litellm", "config.yaml")))

    @patch('metaclaw.os.path.exists', return_value=True)
    @patch('metaclaw.os.path.getmtime', return_value=12345)
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    @patch('metaclaw.os.listdir', return_value=[])
    def test_structure(self, mock_listdir, mock_file, mock_mtime, mock_exists):
        struct = self.mc.structure()
        self.assertIn("tiers", struct)
        self.assertIn("planes", struct)
        self.assertEqual(self.mc._timestamp, 12345)

    @patch('devices.get_hardware_registry')
    def test_hardware(self, mock_get_hardware_registry):
        mock_get_hardware_registry.return_value = {"node1": {}}
        hw = self.mc.hardware()
        self.assertIn("node1", hw)

    @patch.object(MetaClaw, 'hardware')
    def test_map_nodes(self, mock_hardware):
        mock_hardware.return_value = {"node1": {"name": "node1"}}
        nodes = [{"hostname": "node1"}]
        mapped = self.mc.map_nodes(nodes)
        self.assertIn("node1", mapped)

    @patch.object(MetaClaw, 'structure')
    def test_updateCluster(self, mock_structure):
        mock_structure.return_value = {"planes": {}, "services": {}}
        profile = {"nodes": []}
        updated = self.mc.updateCluster(
            profile, "node1", 1, ["control"], {}, False, True, ["cost"]
        )
        self.assertEqual(updated["nodes"][0]["hostname"], "node1")

    @patch('metaclaw.os.path.exists', return_value=False)
    def test_envInstantiate(self, mock_exists):
        # Simply testing it doesn't crash on teardown
        self.mc.envInstantiate(teardown=True)

    @patch.object(MetaClaw, 'structure')
    def test_validate(self, mock_structure):
        mock_structure.return_value = {"services": {}}
        # Testing it doesn't crash
        self.mc.validate()

    @patch.object(MetaClaw, 'saveFile')
    @patch.object(MetaClaw, 'rootdir')
    def test_destructure(self, mock_rootdir, mock_saveFile):
        mock_rootdir.return_value = "/tmp"
        data = {"tiers": {"tier1": {}}, "services": {}}
        self.mc.destructure(data)
        mock_saveFile.assert_called()

    @patch('metaclaw.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='METACLAW_ROOT=/custom/path\n')
    def test_rootdir(self, mock_file, mock_exists):
        root = self.mc.rootdir()
        self.assertEqual(root, "/custom/path")

    @patch('metaclaw.shutil.move')
    @patch('metaclaw.os.makedirs')
    @patch('metaclaw.os.stat')
    def test_backupFile(self, mock_stat, mock_makedirs, mock_move):
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        self.mc.backupFile("/tmp/test.txt")
        mock_move.assert_called()

    @patch('metaclaw.os.path.exists', return_value=True)
    @patch.object(MetaClaw, 'backupFile')
    @patch('metaclaw.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_saveFile(self, mock_file, mock_makedirs, mock_backupFile, mock_exists):
        self.mc.saveFile("/tmp/test.txt", "content", backup=True)
        mock_backupFile.assert_called()
        mock_file().write.assert_called_with("content")

class TestMarkdown(unittest.TestCase):
    @patch('metaclaw.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='# Hello')
    def test___init__(self, mock_file, mock_exists):
        md = Markdown("test.md")
        self.assertEqual(md.raw_text, "# Hello")

    def test_toHtml(self):
        md = Markdown()
        md.raw_text = "# Title"
        html = md.toHtml()
        self.assertIn("<h1>Title</h1>", html)

    def test_parse_ast(self):
        md = Markdown()
        md.raw_text = "- Item 1\n- Item 2"
        self.assertTrue(md.parse_ast())

    @patch.object(MetaClaw, 'saveFile')
    @patch.object(MetaClaw, 'structure')
    def test_metaclawSetup(self, mock_structure, mock_saveFile):
        mock_structure.return_value = {"services": {}}
        md = Markdown()
        md.metaclawSetup()
        mock_saveFile.assert_called()

if __name__ == '__main__':
    unittest.main()
