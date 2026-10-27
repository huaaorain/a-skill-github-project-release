#!/usr/bin/env python3
"""Offline smoke tests for release_manager.py."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("release_manager.py")
sys.path.insert(0, str(SCRIPT.parent))
import release_manager  # noqa: E402


class ReleaseManagerSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        test_tmp_root = Path(__file__).parent / ".test-tmp"
        test_tmp_root.mkdir(exist_ok=True)
        self.root = test_tmp_root / f"case-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.run_cmd(["git", "init", "-b", "main"])
        self.run_cmd(["git", "config", "user.name", "Release Test"])
        self.run_cmd(["git", "config", "user.email", "release@example.test"])
        (self.root / ".gitignore").write_text("release-build/\n", encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "src" / "app.txt").write_text("source\n", encoding="utf-8")
        (self.root / "docs" / "assets").mkdir(parents=True)
        (self.root / "docs" / "assets" / "main.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
        (self.root / "README.md").write_text(
            "# 示例项目\n\n[English](README.en.md)\n\n![Main](docs/assets/main.png)\n\n"
            "<!-- release-catalog:start -->\nempty\n<!-- release-catalog:end -->\n",
            encoding="utf-8",
        )
        (self.root / "README.en.md").write_text(
            "# Demo\n\n[简体中文](README.md)\n\n![Main](docs/assets/main.png)\n\n"
            "<!-- release-catalog:start -->\nempty\n<!-- release-catalog:end -->\n",
            encoding="utf-8",
        )
        self.cli("init", "--root", str(self.root), "--repo", "example/demo")
        self.spec_path = self.root / ".github" / "release-spec.json"
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["project"]["description"] = "A test project."
        spec["project"]["topics"] = ["testing"]
        spec["readme"]["locales"] = [
            {
                "path": "README.md",
                "label": "简体中文",
                "catalog_labels": {
                    "latest": "最新版本",
                    "version": "版本",
                    "published": "发布时间",
                    "release_notes": "发布说明",
                    "downloads": "全部版本下载",
                    "open": "打开",
                    "source_zip": "源代码（zip）",
                    "source_tar": "源代码（tar.gz）",
                },
            },
            {
                "path": "README.en.md",
                "label": "English",
                "catalog_labels": {
                    "latest": "Latest",
                    "downloads": "All version downloads",
                },
            },
        ]
        release_build = self.root / "release-build"
        release_build.mkdir()
        (release_build / "demo.zip").write_bytes(b"release asset")
        spec["artifacts"] = [
            {
                "path": "release-build/demo.zip",
                "role": "standard",
                "description": "Demo application archive.",
                "required": True,
                "download_name": "demo.zip",
            }
        ]
        spec["screenshots"] = [
            {
                "path": "docs/assets/main.png",
                "description": "Main demo view.",
            }
        ]
        self.spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        self.run_cmd(["git", "add", "."])
        self.run_cmd(["git", "commit", "-m", "Initial project"])

    def tearDown(self) -> None:
        test_tmp_root = (Path(__file__).parent / ".test-tmp").resolve()
        resolved = self.root.resolve()
        if test_tmp_root not in resolved.parents:
            raise RuntimeError(f"Refusing to remove unexpected test path: {resolved}")

        def force_remove(function, path, _error) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)

        shutil.rmtree(resolved, onexc=force_remove)

    def run_cmd(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            cwd=self.root,
            check=check,
            capture_output=True,
            text=True,
        )

    def cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return self.run_cmd([sys.executable, str(SCRIPT), *args], check=check)

    def test_manifest_notes_and_preflight(self) -> None:
        self.cli(
            "manifest",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v0.1.0",
            "--output",
            str(self.root / "release-build"),
        )
        manifest = json.loads((self.root / "release-build" / "release-manifest.json").read_text())
        self.assertEqual(manifest["artifacts"][0]["name"], "demo.zip")
        self.assertEqual(len(manifest["artifacts"][0]["sha256"]), 64)
        summary = self.root / "release-build" / "summary.md"
        summary.write_text(
            "## Summary\n\nInitial release.\n\n"
            "## Highlights\n\n- Works.\n\n"
            "## Compatibility and upgrade notes\n\nNone.\n",
            encoding="utf-8",
        )
        notes = self.root / "release-build" / "release-notes.md"
        self.cli(
            "render-notes",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v0.1.0",
            "--summary",
            str(summary),
            "--manifest",
            str(self.root / "release-build" / "release-manifest.json"),
            "--output",
            str(notes),
        )
        self.assertIn("## Release files", notes.read_text(encoding="utf-8"))
        self.assertIn(
            "demo.zip",
            (self.root / "release-build" / "FILE_MANIFEST.md").read_text(encoding="utf-8"),
        )
        self.cli(
            "preflight",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v0.1.0",
            "--notes",
            str(notes),
        )
        result = self.cli(
            "create-release",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v0.1.0",
            "--target",
            "HEAD",
            "--notes",
            str(notes),
            "--assets",
            str(self.root / "release-build" / "demo.zip"),
            str(self.root / "release-build" / "release-manifest.json"),
            str(self.root / "release-build" / "FILE_MANIFEST.md"),
            str(self.root / "release-build" / "SHA256SUMS.txt"),
            "--dry-run",
        )
        self.assertIn('"draft": true', result.stdout)

    def test_first_release_defaults_to_0_1_0(self) -> None:
        notes = self.root / "release-build" / "notes.md"
        notes.write_text(
            "## Summary\n\nInitial release.\n\n"
            "## Highlights\n\n- Works.\n\n"
            "## Compatibility and upgrade notes\n\nNone.\n\n"
            "## Release files\n\nPending.\n",
            encoding="utf-8",
        )
        result = self.cli(
            "preflight",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v1.0.0",
            "--notes",
            str(notes),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("first release must use v0.1.0", result.stderr)

    def test_catalog_updates_only_marker_block(self) -> None:
        releases = [
            {
                "tag_name": "v1.1.0",
                "name": "Demo v1.1.0",
                "draft": False,
                "published_at": "2026-10-27T00:00:00Z",
                "html_url": "https://github.com/example/demo/releases/tag/v1.1.0",
                "assets": [
                    {
                        "name": "demo.zip",
                        "size": 13,
                        "browser_download_url": "https://example.test/v1.1.0/demo.zip",
                    }
                ],
            },
            {
                "tag_name": "v1.0.0",
                "name": "Demo v1.0.0",
                "draft": False,
                "published_at": "2026-10-26T00:00:00Z",
                "html_url": "https://github.com/example/demo/releases/tag/v1.0.0",
                "assets": [],
            },
        ]
        fixture = self.root / "releases.json"
        fixture.write_text(json.dumps(releases), encoding="utf-8")
        self.cli(
            "catalog",
            "--spec",
            str(self.spec_path),
            "--from-json",
            str(fixture),
            "--write",
        )
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("全部版本下载", readme)
        self.assertIn("最新版本", readme)
        self.assertIn("v1.1.0", readme)
        self.assertIn("v1.0.0", readme)
        self.assertEqual(readme.count("<!-- release-catalog:start -->"), 1)
        self.assertIn("# 示例项目", readme)
        english = (self.root / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("All version downloads", english)
        self.assertIn("Latest:", english)

    def test_tracked_release_artifact_is_rejected(self) -> None:
        tracked = self.root / "tracked.bin"
        tracked.write_bytes(b"not for git")
        self.run_cmd(["git", "add", "tracked.bin"])
        self.run_cmd(["git", "commit", "-m", "Track binary"])
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["artifacts"][0]["path"] = "tracked.bin"
        self.spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        result = self.cli(
            "manifest",
            "--spec",
            str(self.spec_path),
            "--tag",
            "v1.0.0",
            "--output",
            str(self.root / "release-build"),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tracked by Git", result.stderr)

    def test_archive_is_deterministic(self) -> None:
        source = self.root / "portable"
        source.mkdir()
        (source / "app.exe").write_bytes(b"binary")
        (source / "readme.txt").write_text("hello", encoding="utf-8")
        first = self.root / "one.zip"
        second = self.root / "two.zip"
        self.cli("archive", "--source", str(source), "--output", str(first))
        self.cli("archive", "--source", str(source), "--output", str(second))
        first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
        second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
        self.assertEqual(first_hash, second_hash)

    def test_release_note_update_requires_confirmation(self) -> None:
        notes = self.root / "release-build" / "notes.md"
        notes.write_text("## Summary\n", encoding="utf-8")
        result = self.cli(
            "update-release-notes",
            "--repo",
            "example/demo",
            "--tag",
            "v1.0.0",
            "--notes",
            str(notes),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm", result.stderr)

    def test_find_release_includes_drafts(self) -> None:
        with mock.patch.object(
            release_manager,
            "list_releases",
            return_value=[{"tag_name": "v1.0.0", "draft": True, "id": 42}],
        ):
            release = release_manager.find_release("example/demo", "v1.0.0")
        self.assertEqual(release["id"], 42)

    def test_asset_download_requests_binary_media_type(self) -> None:
        response = mock.MagicMock()
        response.read.return_value = b"manifest"
        response.__enter__.return_value = response
        with (
            mock.patch.object(release_manager.urllib.request, "urlopen", return_value=response) as request,
            mock.patch.object(release_manager, "github_token", return_value="test-token"),
        ):
            data = release_manager.api_download(
                "https://api.github.com/repos/example/demo/releases/assets/1",
                accept="application/octet-stream",
            )
        self.assertEqual(data, b"manifest")
        prepared = request.call_args.args[0]
        self.assertEqual(prepared.get_header("Accept"), "application/octet-stream")


if __name__ == "__main__":
    unittest.main()
