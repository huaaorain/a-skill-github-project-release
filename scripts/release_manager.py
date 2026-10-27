#!/usr/bin/env python3
"""Deterministic helpers for the github-project-release skill."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import http.client
import json
import mimetypes
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


API_ROOT = "https://api.github.com"
UPLOAD_HOST = "uploads.github.com"
MAX_ASSET_SIZE = 2 * 1024**3
CATALOG_START = "<!-- release-catalog:start -->"
CATALOG_END = "<!-- release-catalog:end -->"
DEFAULT_CATALOG_LABELS = {
    "latest": "Latest",
    "version": "Version",
    "published": "Published",
    "release_notes": "Release notes",
    "downloads": "All version downloads",
    "open": "Open",
    "source_zip": "Source code (zip)",
    "source_tar": "Source code (tar.gz)",
    "no_assets": "No uploaded assets.",
    "no_releases": "No published releases yet.",
}
DEFAULT_EXCLUDES = (
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
)
SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
)


class ReleaseError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReleaseError(message)


def run(
    args: list[str],
    cwd: Path | None = None,
    *,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=text,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if text else result.stderr.decode(errors="replace")
        stdout = result.stdout.strip() if text else result.stdout.decode(errors="replace")
        fail(f"Command failed ({' '.join(args)}): {stderr or stdout}")
    return result


def project_root_from_spec(spec_path: Path) -> Path:
    result = run(
        ["git", "-C", str(spec_path.parent), "rev-parse", "--show-toplevel"],
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip()).resolve()
    if spec_path.parent.name == ".github":
        return spec_path.parent.parent.resolve()
    return spec_path.parent.resolve()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"File not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_json_atomic(path: Path, value: dict) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_spec(path: str) -> tuple[Path, Path, dict]:
    spec_path = Path(path).expanduser().resolve()
    spec = load_json(spec_path)
    if spec.get("schema_version") != 1:
        fail("release spec must use schema_version 1")
    if spec.get("artifact_policy") != "release-only":
        fail("artifact_policy must be 'release-only' for this skill")
    root = project_root_from_spec(spec_path)
    return root, spec_path, spec


def readme_locales(spec: dict) -> list[dict]:
    readme = spec.get("readme", {})
    locales = readme.get("locales")
    if not isinstance(locales, list) or not locales:
        return [
            {
                "path": readme.get("path", "README.md"),
                "label": "default",
                "catalog_labels": dict(DEFAULT_CATALOG_LABELS),
            }
        ]
    result: list[dict] = []
    seen: set[str] = set()
    for locale in locales:
        if not isinstance(locale, dict):
            fail("each readme locale must be an object")
        path = str(locale.get("path", "")).strip()
        label = str(locale.get("label", "")).strip()
        if not path or not label:
            fail("each readme locale needs path and label")
        if path in seen:
            fail(f"duplicate localized README path: {path}")
        seen.add(path)
        labels = dict(DEFAULT_CATALOG_LABELS)
        override = locale.get("catalog_labels", {})
        if override and not isinstance(override, dict):
            fail(f"catalog_labels must be an object for {path}")
        labels.update(override or {})
        result.append({"path": path, "label": label, "catalog_labels": labels})
    return result


def repo_name(spec: dict) -> str:
    value = str(spec.get("project", {}).get("repository", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        fail("project.repository must look like OWNER/REPO")
    return value


def safe_project_path(root: Path, raw_path: str, label: str) -> Path:
    path = (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        fail(f"{label} must stay inside the project root: {raw_path}")
    return path


def is_git_tracked(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    result = run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative.as_posix()],
        check=False,
    )
    return result.returncode == 0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(root: Path, *args: str, default: str = "") -> str:
    result = run(["git", "-C", str(root), *args], check=False)
    return result.stdout.strip() if result.returncode == 0 else default


def github_token(required: bool = False) -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if required and not token:
        fail("GITHUB_TOKEN or GH_TOKEN is required for this operation")
    return token


def api_request(
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    required_auth: bool = False,
    accept: str = "application/vnd.github+json",
) -> dict | list | None:
    url = path if path.startswith("https://") else f"{API_ROOT}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": accept,
        "User-Agent": "github-project-release-skill",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = github_token(required=required_auth)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            if not body:
                return None
            return json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"GitHub API {method} {path} failed with HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(f"GitHub API request failed: {exc.reason}")


def api_download(url: str) -> bytes:
    headers = {"User-Agent": "github-project-release-skill"}
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            fail(f"Download not found: {url}")
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"Download failed with HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(f"Download failed: {exc.reason}")


def upload_asset(repo: str, release_id: int, file_path: Path, asset_name: str) -> dict:
    token = github_token(required=True)
    size = file_path.stat().st_size
    if size > MAX_ASSET_SIZE:
        fail(f"Asset exceeds GitHub's usual 2 GiB per-file limit: {file_path}")
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    quoted_name = urllib.parse.quote(asset_name, safe="")
    path = f"/repos/{repo}/releases/{release_id}/assets?name={quoted_name}"
    context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(UPLOAD_HOST, timeout=600, context=context)
    try:
        connection.putrequest("POST", path)
        connection.putheader("Authorization", f"Bearer {token}")
        connection.putheader("Accept", "application/vnd.github+json")
        connection.putheader("X-GitHub-Api-Version", "2022-11-28")
        connection.putheader("User-Agent", "github-project-release-skill")
        connection.putheader("Content-Type", content_type)
        connection.putheader("Content-Length", str(size))
        connection.endheaders()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                connection.send(chunk)
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 201:
            fail(f"Asset upload failed with HTTP {response.status}: {body}")
        return json.loads(body)
    finally:
        connection.close()


def list_releases(repo: str, include_drafts: bool = True) -> list[dict]:
    releases: list[dict] = []
    page = 1
    while True:
        result = api_request("GET", f"/repos/{repo}/releases?per_page=100&page={page}")
        if not isinstance(result, list):
            fail("Unexpected releases API response")
        releases.extend(result)
        if not include_drafts:
            releases = [release for release in releases if not release.get("draft")]
        if len(result) < 100:
            break
        page += 1
    return releases


def find_release(repo: str, tag: str) -> dict | None:
    # The by-tag endpoint omits draft releases, so search the authenticated
    # release list as well. This keeps draft creation and publishing resumable.
    for release in list_releases(repo, include_drafts=True):
        if release.get("tag_name") == tag:
            return release
    return None


def remote_tag_commit(repo: str, tag: str) -> str | None:
    try:
        reference = api_request(
            "GET",
            f"/repos/{repo}/git/ref/tags/{urllib.parse.quote(tag, safe='')}",
        )
    except ReleaseError as exc:
        if "HTTP 404" in str(exc):
            return None
        raise
    if not isinstance(reference, dict):
        fail("GitHub returned an unexpected tag reference")
    target = reference.get("object", {})
    if target.get("type") == "tag":
        annotated = api_request(
            "GET",
            f"/repos/{repo}/git/tags/{urllib.parse.quote(target.get('sha', ''), safe='')}",
        )
        if isinstance(annotated, dict):
            target = annotated.get("object", {})
    return target.get("sha")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def init_spec(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        fail(f"Project root does not exist: {root}")
    output = root / ".github" / "release-spec.json"
    if output.exists():
        fail(f"Release spec already exists: {output}")
    owner, name = args.repo.split("/", 1)
    value = {
        "schema_version": 1,
        "project": {
            "name": root.name,
            "description": "",
            "repository": f"{owner}/{name}",
            "homepage": "",
            "topics": [],
        },
        "release": {
            "tag_prefix": args.tag_prefix,
            "draft": True,
            "prerelease": False,
        },
        "artifact_policy": "release-only",
        "readme": {
            "path": "README.md",
            "catalog_start": CATALOG_START,
            "catalog_end": CATALOG_END,
        },
        "screenshots": [],
        "artifacts": [],
    }
    write_json_atomic(output, value)
    print(output)


def archive_directory(args: argparse.Namespace) -> None:
    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_dir():
        fail(f"Source directory does not exist: {source}")
    try:
        output.relative_to(source)
        fail("Archive output must not be inside the source directory")
    except ValueError:
        pass
    output.parent.mkdir(parents=True, exist_ok=True)
    excludes = DEFAULT_EXCLUDES + tuple(args.exclude or [])
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(fnmatch.fnmatch(part, pattern) for part in relative.parts for pattern in excludes):
            continue
        if path.is_symlink():
            fail(f"Symlinks are not allowed in release archives: {relative}")
        if path.is_file():
            files.append(path)
    if not files:
        fail("Source directory contains no archiveable files")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with path.open("rb") as source_handle:
                archive.writestr(info, source_handle.read())
    print(output)


def validate_artifact_entries(root: Path, spec: dict) -> list[dict]:
    artifacts = spec.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        fail("release spec must contain at least one artifact")
    names: set[str] = set()
    checked: list[dict] = []
    for entry in artifacts:
        if not isinstance(entry, dict):
            fail("each artifact entry must be an object")
        raw_path = str(entry.get("path", "")).strip()
        description = str(entry.get("description", "")).strip()
        role = str(entry.get("role", "")).strip()
        if not raw_path or not description or not role:
            fail("each artifact needs path, role, and description")
        path = safe_project_path(root, raw_path, "artifact")
        if not path.is_file():
            fail(f"Artifact is missing or is not a file: {path}")
        if path.stat().st_size > MAX_ASSET_SIZE:
            fail(f"Artifact exceeds GitHub's usual 2 GiB per-file limit: {path}")
        if is_git_tracked(root, path):
            fail(f"Release artifact is tracked by Git: {path.relative_to(root)}")
        name = str(entry.get("download_name") or path.name).strip()
        if not name or "/" in name or "\\" in name:
            fail(f"Invalid download_name for {path.name}")
        if name in names:
            fail(f"Duplicate release asset name: {name}")
        names.add(name)
        checked.append({**entry, "resolved_path": str(path), "download_name": name})
    return checked


def build_manifest(args: argparse.Namespace) -> None:
    root, _, spec = load_spec(args.spec)
    artifacts = validate_artifact_entries(root, spec)
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    commit = git_value(root, "rev-parse", "HEAD")
    if not commit:
        fail("Could not determine the current Git commit")
    manifest = {
        "schema_version": 1,
        "project": spec["project"]["name"],
        "repository": repo_name(spec),
        "tag": args.tag,
        "commit": commit,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "artifact_policy": "release-only",
        "artifacts": [],
    }
    checksum_lines: list[str] = []
    for entry in artifacts:
        path = Path(entry["resolved_path"])
        digest = sha256_file(path)
        size = path.stat().st_size
        item = {
            "name": entry["download_name"],
            "path": path.relative_to(root).as_posix(),
            "role": entry["role"],
            "description": entry["description"],
            "required": bool(entry.get("required", True)),
            "size": size,
            "sha256": digest,
            "content_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        }
        manifest["artifacts"].append(item)
        checksum_lines.append(f"{digest}  {entry['download_name']}")
    manifest_path = output_dir / "release-manifest.json"
    write_json_atomic(manifest_path, manifest)
    table = [
        "# Release File Manifest",
        "",
        f"- Project: {manifest['project']}",
        f"- Tag: `{args.tag}`",
        f"- Commit: `{commit}`",
        "",
        "| File | Role | Purpose | Size | SHA-256 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in manifest["artifacts"]:
        table.append(
            "| "
            + " | ".join(
                (
                    md_cell(f"`{item['name']}`"),
                    md_cell(item["role"]),
                    md_cell(item["description"]),
                    human_size(item["size"]),
                    f"`{item['sha256']}`",
                )
            )
            + " |"
        )
    table.extend(
        (
            "",
            "GitHub also generates source-code ZIP and TAR archives for the release tag.",
            "",
        )
    )
    write_text_atomic(output_dir / "FILE_MANIFEST.md", "\n".join(table))
    write_text_atomic(
        output_dir / "SHA256SUMS.txt",
        "\n".join(sorted(checksum_lines, key=lambda line: line.split("  ", 1)[1])) + "\n",
    )
    print(manifest_path)
    print(output_dir / "FILE_MANIFEST.md")
    print(output_dir / "SHA256SUMS.txt")


def build_context(args: argparse.Namespace) -> None:
    root, _, spec = load_spec(args.spec)
    repo = repo_name(spec)
    tag_prefix = str(spec.get("release", {}).get("tag_prefix", "v"))
    current_commit = git_value(root, "rev-parse", "HEAD")
    previous = args.previous
    if not previous:
        previous = git_value(
            root,
            "describe",
            "--tags",
            "--abbrev=0",
            f"--match={tag_prefix}*",
            "HEAD^",
        )
    commits_text = ""
    changed_text = ""
    previous_commit = ""
    if previous:
        previous_commit = git_value(root, "rev-list", "-n", "1", previous)
        commits_text = git_value(
            root,
            "log",
            "--reverse",
            "--pretty=format:%H%x09%s",
            f"{previous}..HEAD",
        )
        changed_text = git_value(root, "diff", "--name-status", f"{previous}...HEAD")
    commits = []
    for line in commits_text.splitlines():
        commit, _, subject = line.partition("\t")
        if commit:
            commits.append({"sha": commit, "subject": subject})
    changed_files = []
    for line in changed_text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changed_files.append({"status": parts[0], "path": parts[-1]})
    context = {
        "repository": repo,
        "tag": args.tag,
        "current_commit": current_commit,
        "previous_tag": previous or None,
        "previous_commit": previous_commit or None,
        "commits": commits,
        "changed_files": changed_files,
        "working_tree": git_value(root, "status", "--porcelain"),
        "diff_stat": git_value(root, "diff", "--stat", f"{previous}...HEAD") if previous else "",
        "previous_manifest": None,
    }
    if previous and not args.no_api:
        previous_release = find_release(repo, previous)
        if previous_release:
            context["previous_release"] = {
                "tag": previous_release.get("tag_name"),
                "name": previous_release.get("name"),
                "published_at": previous_release.get("published_at"),
                "html_url": previous_release.get("html_url"),
            }
            manifest_asset = next(
                (asset for asset in previous_release.get("assets", []) if asset.get("name") == "release-manifest.json"),
                None,
            )
            if manifest_asset:
                try:
                    context["previous_manifest"] = json.loads(
                        api_download(manifest_asset["browser_download_url"]).decode("utf-8")
                    )
                except (UnicodeDecodeError, json.JSONDecodeError):
                    context["previous_manifest_error"] = "Previous release manifest was not valid JSON."
    output = Path(args.output).expanduser().resolve()
    write_json_atomic(output, context)
    print(output)


def render_notes(args: argparse.Namespace) -> None:
    _, _, spec = load_spec(args.spec)
    summary_path = Path(args.summary).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    summary = summary_path.read_text(encoding="utf-8").strip()
    manifest = load_json(manifest_path)
    if "{{" in summary:
        fail("Release summary still contains template placeholders")
    required = ("## Summary", "## Highlights", "## Compatibility and upgrade notes")
    missing = [heading for heading in required if heading not in summary]
    if missing:
        fail(f"Release summary is missing required sections: {', '.join(missing)}")
    repo = repo_name(spec)
    tag = args.tag
    download_base = f"https://github.com/{repo}/releases/download/{urllib.parse.quote(tag, safe='')}"
    lines = [
        summary,
        "",
        "## Release files",
        "",
        "| File | Role | Purpose | Size | Download | SHA-256 |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in manifest.get("artifacts", []):
        name = item["name"]
        url = f"{download_base}/{urllib.parse.quote(name, safe='')}"
        lines.append(
            "| "
            + " | ".join(
                (
                    md_cell(f"`{name}`"),
                    md_cell(item["role"]),
                    md_cell(item["description"]),
                    human_size(int(item["size"])),
                    f"[Download]({url})",
                    f"`{item['sha256']}`",
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "## Release metadata",
            "",
            "| File | Purpose |",
            "| --- | --- |",
            "| `release-manifest.json` | Machine-readable release and checksum inventory. |",
            "| `FILE_MANIFEST.md` | Human-readable file inventory for this release. |",
            "| `SHA256SUMS.txt` | SHA-256 checksums for downloadable artifacts. |",
            "",
            "## Source",
            "",
            f"- Commit: `{manifest['commit']}`",
            f"- [Source code (zip)](https://github.com/{repo}/archive/refs/tags/{urllib.parse.quote(tag, safe='')}.zip)",
            f"- [Source code (tar.gz)](https://github.com/{repo}/archive/refs/tags/{urllib.parse.quote(tag, safe='')}.tar.gz)",
            "",
            "Verify downloaded assets against `SHA256SUMS.txt`.",
            "",
        )
    )
    output = Path(args.output).expanduser().resolve()
    write_text_atomic(output, "\n".join(lines))
    print(output)


def scan_tracked_secrets(root: Path) -> list[str]:
    result = run(["git", "-C", str(root), "ls-files", "-z"], check=False)
    if result.returncode != 0:
        return []
    findings: list[str] = []
    for relative in result.stdout.split("\0"):
        if not relative:
            continue
        path = root / relative
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(relative)
                break
    return findings


def preflight(args: argparse.Namespace) -> None:
    root, _, spec = load_spec(args.spec)
    repo_name(spec)
    artifacts = validate_artifact_entries(root, spec)
    tag = args.tag
    tag_prefix = str(spec.get("release", {}).get("tag_prefix", ""))
    if tag_prefix and not tag.startswith(tag_prefix):
        fail(f"Tag {tag} does not use configured prefix {tag_prefix}")
    if git_value(root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}"):
        fail(f"Tag already exists: {tag}")
    locales = readme_locales(spec)
    start = spec["readme"].get("catalog_start", CATALOG_START)
    end = spec["readme"].get("catalog_end", CATALOG_END)
    screenshots = spec.get("screenshots", [])
    if not screenshots:
        fail("At least one functional screenshot or diagram is required")
    screenshot_paths: list[str] = []
    for screenshot in screenshots:
        path = safe_project_path(root, screenshot.get("path", ""), "screenshot")
        if not path.is_file():
            fail(f"Functional image is missing: {path}")
        relative = path.relative_to(root).as_posix()
        screenshot_paths.append(relative)
        if not str(screenshot.get("description", "")).strip():
            fail(f"Screenshot needs a description: {relative}")
    for locale in locales:
        readme_path = safe_project_path(root, locale["path"], "README")
        if not readme_path.is_file():
            fail(f"README does not exist: {readme_path}")
        readme = readme_path.read_text(encoding="utf-8")
        if readme.count(start) != 1 or readme.count(end) != 1 or readme.index(start) > readme.index(end):
            fail(f"{locale['path']} must contain exactly one ordered release-catalog marker pair")
        for relative in screenshot_paths:
            if relative not in readme:
                fail(f"Functional image is not referenced by {locale['path']}: {relative}")
        if len(locales) > 1:
            for other in locales:
                if other["path"] != locale["path"] and other["path"] not in readme:
                    fail(f"{locale['path']} needs a language link to {other['path']}")
    notes_path = Path(args.notes).expanduser().resolve()
    notes = notes_path.read_text(encoding="utf-8")
    for heading in ("## Summary", "## Highlights", "## Compatibility and upgrade notes", "## Release files"):
        if heading not in notes:
            fail(f"Release notes are missing {heading}")
    untracked_build = [
        Path(entry["resolved_path"]).name
        for entry in artifacts
        if run(
            ["git", "-C", str(root), "check-ignore", "--quiet", str(Path(entry["resolved_path"]))],
            check=False,
        ).returncode
        != 0
    ]
    if untracked_build:
        fail(
            "Release artifacts are not covered by .gitignore: "
            + ", ".join(untracked_build)
        )
    secret_files = scan_tracked_secrets(root)
    if secret_files:
        fail("Likely secrets found in tracked files: " + ", ".join(secret_files))
    print(f"preflight passed for {tag} with {len(artifacts)} artifact(s)")


def create_repo(args: argparse.Namespace) -> None:
    if not args.confirm_create:
        fail("create-repo requires --confirm-create after the user approves owner, name, and visibility")
    _, _, spec = load_spec(args.spec)
    repo = repo_name(spec)
    owner, name = repo.split("/", 1)
    current = api_request("GET", "/user", required_auth=True)
    if not isinstance(current, dict):
        fail("Could not determine the authenticated GitHub user")
    login = current["login"]
    payload = {
        "name": name,
        "private": args.visibility == "private",
        "description": spec["project"].get("description", ""),
        "homepage": spec["project"].get("homepage", ""),
        "has_issues": True,
        "has_projects": True,
        "has_wiki": False,
        "auto_init": False,
    }
    path = "/user/repos" if owner == login else f"/orgs/{urllib.parse.quote(owner, safe='')}/repos"
    result = api_request("POST", path, payload, required_auth=True)
    if not isinstance(result, dict):
        fail("Repository creation returned an unexpected response")
    topics = [str(topic) for topic in spec["project"].get("topics", []) if str(topic).strip()]
    if topics:
        api_request(
            "PUT",
            f"/repos/{repo}/topics",
            {"names": topics},
            required_auth=True,
            accept="application/vnd.github+json",
        )
    print(f"created https://github.com/{repo}")


def update_repo(args: argparse.Namespace) -> None:
    if not args.confirm_update:
        fail("update-repo requires --confirm-update")
    _, _, spec = load_spec(args.spec)
    repo = repo_name(spec)
    project = spec["project"]
    api_request(
        "PATCH",
        f"/repos/{repo}",
        {
            "description": project.get("description", ""),
            "homepage": project.get("homepage", ""),
        },
        required_auth=True,
    )
    topics = [str(topic) for topic in project.get("topics", []) if str(topic).strip()]
    api_request(
        "PUT",
        f"/repos/{repo}/topics",
        {"names": topics},
        required_auth=True,
    )
    print(f"updated repository metadata for {repo}")


def repo_info(args: argparse.Namespace) -> None:
    result = api_request("GET", f"/repos/{args.repo}")
    if not isinstance(result, dict):
        fail("Could not read repository")
    print(
        json.dumps(
            {
                "full_name": result.get("full_name"),
                "description": result.get("description"),
                "default_branch": result.get("default_branch"),
                "private": result.get("private"),
                "html_url": result.get("html_url"),
                "topics": result.get("topics", []),
                "permissions": result.get("permissions", {}),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def auth_info(_: argparse.Namespace) -> None:
    result = api_request("GET", "/user", required_auth=True)
    if not isinstance(result, dict):
        fail("Could not read authenticated user")
    print(json.dumps({"login": result.get("login"), "type": result.get("type")}, indent=2))


def create_release(args: argparse.Namespace) -> None:
    root, _, spec = load_spec(args.spec)
    repo = repo_name(spec)
    if not args.dry_run and find_release(repo, args.tag):
        fail(f"Release already exists: {args.tag}")
    notes_path = Path(args.notes).expanduser().resolve()
    notes = notes_path.read_text(encoding="utf-8")
    asset_paths = [Path(path).expanduser().resolve() for path in args.assets]
    asset_names = {path.name for path in asset_paths}
    required_metadata = {"release-manifest.json", "FILE_MANIFEST.md", "SHA256SUMS.txt"}
    missing_metadata = sorted(required_metadata - asset_names)
    if missing_metadata:
        fail("create-release assets are missing: " + ", ".join(missing_metadata))
    manifest_path = next(path for path in asset_paths if path.name == "release-manifest.json")
    manifest = load_json(manifest_path)
    if manifest.get("tag") != args.tag:
        fail("release-manifest.json tag does not match --tag")
    target_commit = git_value(root, "rev-parse", f"{args.target}^{{commit}}")
    if not target_commit:
        fail(f"Could not resolve target commit: {args.target}")
    if manifest.get("commit") != target_commit:
        fail("release-manifest.json commit does not match --target")
    if not args.dry_run:
        existing_tag_commit = remote_tag_commit(repo, args.tag)
        if existing_tag_commit and existing_tag_commit != target_commit:
            fail("Existing tag points to a different commit: " + args.tag)
    manifest_names = {item.get("name") for item in manifest.get("artifacts", [])}
    missing_artifacts = sorted(name for name in manifest_names if name not in asset_names)
    if missing_artifacts:
        fail("Release artifacts listed in the manifest are missing: " + ", ".join(missing_artifacts))
    paths_by_name = {path.name: path for path in asset_paths}
    for item in manifest.get("artifacts", []):
        path = paths_by_name[item["name"]]
        if path.stat().st_size != int(item["size"]) or sha256_file(path) != item["sha256"]:
            fail(f"Release artifact changed after manifest generation: {path.name}")
    payload = {
        "tag_name": args.tag,
        "target_commitish": target_commit,
        "name": args.name or f"{spec['project']['name']} {args.tag}",
        "body": notes,
        "draft": True,
        "prerelease": bool(args.prerelease),
        "generate_release_notes": False,
    }
    if args.dry_run:
        print(json.dumps({**payload, "repository": repo, "assets": args.assets}, ensure_ascii=False, indent=2))
        return
    result = api_request("POST", f"/repos/{repo}/releases", payload, required_auth=True)
    if not isinstance(result, dict) or "id" not in result:
        fail("Release creation returned an unexpected response")
    print(f"created draft {result.get('html_url')}")
    upload_assets_to_release(repo, result, asset_paths)


def release_by_tag_or_fail(repo: str, tag: str) -> dict:
    release = find_release(repo, tag)
    if not release:
        fail(f"Release not found: {tag}")
    return release


def upload_assets_to_release(repo: str, release: dict, files: list[Path]) -> None:
    existing = {asset["name"]: asset for asset in release.get("assets", [])}
    for path in files:
        if not path.is_file():
            fail(f"Asset does not exist: {path}")
        name = path.name
        if name in existing:
            if int(existing[name].get("size", -1)) == path.stat().st_size:
                print(f"asset already present, skipped: {name}")
                continue
            fail(f"Release already has a different asset named {name}")
        uploaded = upload_asset(repo, int(release["id"]), path, name)
        existing[name] = uploaded
        print(f"uploaded {name} ({human_size(path.stat().st_size)})")


def upload_assets(args: argparse.Namespace) -> None:
    repo = args.repo
    release = release_by_tag_or_fail(repo, args.tag)
    upload_assets_to_release(repo, release, [Path(path).expanduser().resolve() for path in args.files])


def publish_release(args: argparse.Namespace) -> None:
    if not args.confirm:
        fail("publish-release requires --confirm after verification and user approval")
    release = release_by_tag_or_fail(args.repo, args.tag)
    if not release.get("draft"):
        print("release is already published")
        return
    assets = {asset["name"]: asset for asset in release.get("assets", [])}
    required_metadata = {"release-manifest.json", "FILE_MANIFEST.md", "SHA256SUMS.txt"}
    missing_metadata = sorted(required_metadata - set(assets))
    if missing_metadata:
        fail("Draft release is missing metadata assets: " + ", ".join(missing_metadata))
    manifest = json.loads(api_download(assets["release-manifest.json"]["browser_download_url"]))
    if manifest.get("tag") != args.tag:
        fail("Draft release manifest tag does not match the release tag")
    missing_artifacts = []
    for item in manifest.get("artifacts", []):
        asset = assets.get(item.get("name"))
        if not asset or int(asset.get("size", -1)) != int(item.get("size", -2)):
            missing_artifacts.append(str(item.get("name")))
    if missing_artifacts:
        fail("Draft release assets do not match the manifest: " + ", ".join(missing_artifacts))
    result = api_request(
        "PATCH",
        f"/repos/{args.repo}/releases/{release['id']}",
        {"draft": False},
        required_auth=True,
    )
    if isinstance(result, dict):
        print(result.get("html_url"))


def update_release_notes(args: argparse.Namespace) -> None:
    if not args.confirm:
        fail("update-release-notes requires --confirm")
    release = release_by_tag_or_fail(args.repo, args.tag)
    notes = Path(args.notes).expanduser().resolve().read_text(encoding="utf-8")
    payload = {"body": notes}
    if args.name:
        payload["name"] = args.name
    result = api_request(
        "PATCH",
        f"/repos/{args.repo}/releases/{release['id']}",
        payload,
        required_auth=True,
    )
    if isinstance(result, dict):
        print(result.get("html_url"))


def format_release_date(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value


def catalog_markdown(
    repo: str,
    releases: list[dict],
    labels: dict[str, str] | None = None,
) -> str:
    labels = {**DEFAULT_CATALOG_LABELS, **(labels or {})}
    published = [release for release in releases if not release.get("draft")]
    published.sort(key=lambda release: release.get("published_at") or "", reverse=True)
    if not published:
        return labels["no_releases"]
    latest = published[0]
    lines = [
        f"{labels['latest']}: [{latest.get('name') or latest['tag_name']}]({latest['html_url']})",
        "",
        f"| {labels['version']} | {labels['published']} | {labels['release_notes']} |",
        "| --- | --- | --- |",
    ]
    for release in published:
        tag = release["tag_name"]
        lines.append(
            f"| `{md_cell(tag)}` | {format_release_date(release.get('published_at'))} "
            f"| [{labels['open']}]({release['html_url']}) |"
        )
    lines.extend(("", "<details>", f"<summary><strong>{labels['downloads']}</strong></summary>", ""))
    for release in published:
        tag = release["tag_name"]
        encoded_tag = urllib.parse.quote(tag, safe="")
        lines.extend(
            (
                f"### {release.get('name') or tag}",
                "",
                f"{labels['release_notes']}: [{labels['open']}]({release['html_url']})",
                "",
            )
        )
        assets = release.get("assets", [])
        if assets:
            for asset in assets:
                lines.append(
                    f"- [{asset['name']}]({asset['browser_download_url']}) — "
                    f"{human_size(int(asset.get('size', 0)))}"
                )
        else:
            lines.append(f"- {labels['no_assets']}")
        lines.append(
            f"- [{labels['source_zip']}](https://github.com/{repo}/archive/refs/tags/{encoded_tag}.zip)"
        )
        lines.append(
            f"- [{labels['source_tar']}](https://github.com/{repo}/archive/refs/tags/{encoded_tag}.tar.gz)"
        )
        lines.append("")
    lines.extend(("</details>", ""))
    return "\n".join(lines).strip()


def catalog(args: argparse.Namespace) -> None:
    spec = None
    if args.spec:
        _, _, spec = load_spec(args.spec)
    if args.from_json:
        releases = load_json(Path(args.from_json).expanduser().resolve())
        if not isinstance(releases, list):
            fail("--from-json must contain a JSON array of GitHub releases")
        repo = args.repo
        if not repo:
            for release in releases:
                match = re.match(r"https://github\.com/([^/]+/[^/]+)/releases/", release.get("html_url", ""))
                if match:
                    repo = match.group(1)
                    break
        if not repo:
            fail("Repository is required with --from-json")
    else:
        if spec is None:
            fail("--spec is required unless --from-json is used")
        repo = args.repo or repo_name(spec)
        releases = list_releases(repo)
    if not args.write:
        locales = readme_locales(spec) if spec else [{"catalog_labels": DEFAULT_CATALOG_LABELS}]
        print(catalog_markdown(repo, releases, locales[0]["catalog_labels"]))
        return
    if spec is None:
        fail("--spec is required when writing the catalog")
    root = project_root_from_spec(Path(args.spec).expanduser().resolve())
    start = spec["readme"].get("catalog_start", CATALOG_START)
    end = spec["readme"].get("catalog_end", CATALOG_END)
    for locale in readme_locales(spec):
        readme_path = safe_project_path(root, locale["path"], "README")
        content = readme_path.read_text(encoding="utf-8")
        if content.count(start) != 1 or content.count(end) != 1 or content.index(start) > content.index(end):
            fail(f"{locale['path']} must contain exactly one ordered release-catalog marker pair")
        block = catalog_markdown(repo, releases, locale["catalog_labels"])
        before, remainder = content.split(start, 1)
        _, after = remainder.split(end, 1)
        updated = f"{before}{start}\n{block}\n{end}{after}"
        write_text_atomic(readme_path, updated)
        print(f"updated {readme_path}")


def validate_spec(args: argparse.Namespace) -> None:
    root, _, spec = load_spec(args.spec)
    repo_name(spec)
    validate_artifact_entries(root, spec)
    for screenshot in spec.get("screenshots", []):
        path = safe_project_path(root, screenshot.get("path", ""), "screenshot")
        if not path.is_file():
            fail(f"Screenshot missing: {path}")
    print("release spec is structurally valid")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create .github/release-spec.json")
    p.add_argument("--root", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--tag-prefix", default="v")
    p.set_defaults(func=init_spec)

    p = sub.add_parser("archive", help="create a deterministic ZIP from a directory")
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--exclude", action="append")
    p.set_defaults(func=archive_directory)

    p = sub.add_parser("manifest", help="hash release assets and generate file tables")
    p.add_argument("--spec", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=build_manifest)

    p = sub.add_parser("context", help="collect previous-release and Git context")
    p.add_argument("--spec", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--previous")
    p.add_argument("--output", default="release-build/release-context.json")
    p.add_argument("--no-api", action="store_true")
    p.set_defaults(func=build_context)

    p = sub.add_parser("render-notes", help="append the file manifest to a release summary")
    p.add_argument("--spec", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=render_notes)

    p = sub.add_parser("preflight", help="validate release files, README, notes, and obvious secrets")
    p.add_argument("--spec", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--notes", required=True)
    p.set_defaults(func=preflight)

    p = sub.add_parser("validate-spec", help="validate the release spec")
    p.add_argument("--spec", required=True)
    p.set_defaults(func=validate_spec)

    p = sub.add_parser("auth", help="show the authenticated GitHub account")
    p.set_defaults(func=auth_info)

    p = sub.add_parser("repo-info", help="show repository metadata and permissions")
    p.add_argument("--repo", required=True)
    p.set_defaults(func=repo_info)

    p = sub.add_parser("create-repo", help="create the repository from release-spec metadata")
    p.add_argument("--spec", required=True)
    p.add_argument("--visibility", choices=("public", "private"), required=True)
    p.add_argument("--confirm-create", action="store_true")
    p.set_defaults(func=create_repo)

    p = sub.add_parser("update-repo", help="update description, homepage, and topics")
    p.add_argument("--spec", required=True)
    p.add_argument("--confirm-update", action="store_true")
    p.set_defaults(func=update_repo)

    p = sub.add_parser("create-release", help="create a draft release and upload assets")
    p.add_argument("--spec", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--notes", required=True)
    p.add_argument("--assets", nargs="+", required=True)
    p.add_argument("--name")
    p.add_argument("--prerelease", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=create_release)

    p = sub.add_parser("upload-assets", help="resume asset uploads for an existing draft")
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--files", nargs="+", required=True)
    p.set_defaults(func=upload_assets)

    p = sub.add_parser("publish-release", help="publish a verified draft")
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=publish_release)

    p = sub.add_parser("update-release-notes", help="update an existing release body without changing assets")
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--notes", required=True)
    p.add_argument("--name")
    p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=update_release_notes)

    p = sub.add_parser("catalog", help="render or update the README all-version catalog")
    p.add_argument("--spec")
    p.add_argument("--repo")
    p.add_argument("--from-json")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=catalog)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
