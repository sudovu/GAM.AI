"""Acceptance and unit tests for Android packaging and cross-platform hardware detection."""
import unittest
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from gam_ai.platform.detector import get_memory_info, get_platform_info
from benchmarks.benchmark_resources import get_process_memory_mb
from scripts.build_apk import sync_assets

class TestAndroidAndPlatform(unittest.TestCase):

    def test_cross_platform_memory_detection(self):
        mem = get_memory_info()
        self.assertIn("total_ram_mb", mem)
        self.assertIn("available_ram_mb", mem)
        self.assertGreater(mem["total_ram_mb"], 0)
        self.assertGreater(mem["available_ram_mb"], 0)

    def test_benchmark_process_memory(self):
        rss = get_process_memory_mb()
        self.assertIsInstance(rss, float)
        self.assertGreater(rss, 0.0)

    def test_android_project_structure(self):
        android_root = os.path.join(repo_root, "android")
        self.assertTrue(os.path.isdir(android_root))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "build.gradle")))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "settings.gradle")))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "app", "build.gradle")))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "app", "src", "main", "AndroidManifest.xml")))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "app", "src", "main", "java", "com", "gamai", "app", "MainActivity.java")))
        self.assertTrue(os.path.isfile(os.path.join(android_root, "app", "src", "main", "java", "com", "gamai", "app", "GamAiBridge.java")))

    def test_android_asset_synchronization(self):
        sync_assets(repo_root)
        assets_dir = os.path.join(repo_root, "android", "app", "src", "main", "assets")
        self.assertTrue(os.path.exists(os.path.join(assets_dir, "dashboard.html")))
        self.assertTrue(os.path.exists(os.path.join(assets_dir, "manifest.json")))
        self.assertTrue(os.path.exists(os.path.join(assets_dir, "sw.js")))

    def test_github_actions_workflow_exists(self):
        workflow_path = os.path.join(repo_root, ".github", "workflows", "build-apk.yml")
        self.assertTrue(os.path.isfile(workflow_path))
        with open(workflow_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("assembleRelease", content)
        self.assertIn("upload-artifact", content)

if __name__ == "__main__":
    unittest.main()
