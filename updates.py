"""Manual GitHub Releases update discovery for Claw Metrics.

The privileged plugin backend only reads release metadata. It never extracts or
installs ZIPs: installation is delegated to Decky Loader's own confirmation
and SHA-256-verifying installer. Only this repository's numbered test releases
and exact official GitHub asset URLs are accepted.
"""
import json
import pathlib
import re
import urllib.error
import urllib.request

REPOSITORY = "ikorljan-droid/claw-metrics"
RELEASES_API = "https://api.github.com/repos/" + REPOSITORY + "/releases?per_page=30"
VERSION_PATTERN = re.compile(r"^v?0\.2\.4-test\.(\d+)$")
SHA256_PATTERN = re.compile(r"^sha256:([a-fA-F0-9]{64})$")
MAX_RESPONSE = 2 * 1024 * 1024
MAX_ASSET_BYTES = 30 * 1024 * 1024


def version_number(value):
    if not isinstance(value, str):
        return None
    match = VERSION_PATTERN.fullmatch(value)
    return int(match.group(1)) if match else None


def installed_version(package_file):
    try:
        data = json.loads(pathlib.Path(package_file).read_text(encoding="utf-8"))
        value = data.get("version")
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError("Nije moguće pročitati instaliranu verziju plugina.") from error
    if version_number(value) is None:
        raise RuntimeError("Instalirana verzija nije u podržanom formatu.")
    return value


def latest_compatible_release(releases):
    best = None
    best_number = -1
    if not isinstance(releases, list):
        raise RuntimeError("GitHub nije vratio popis izdanja.")
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        number = version_number(tag)
        if number is None or number <= best_number:
            continue
        file_name = f"ClawMetrics-v0.2.4-test.{number}.zip"
        expected_url = (
            f"https://github.com/{REPOSITORY}/releases/download/"
            f"v0.2.4-test.{number}/{file_name}"
        )
        for asset in release.get("assets", []):
            if not isinstance(asset, dict):
                continue
            match = SHA256_PATTERN.fullmatch(str(asset.get("digest", "")))
            size = asset.get("size")
            if (asset.get("name") == file_name
                    and asset.get("browser_download_url") == expected_url
                    and match and type(size) is int and 100_000 < size < MAX_ASSET_BYTES):
                body = release.get("body")
                notes = body.strip()[:5000] if isinstance(body, str) else ""
                best = {
                    "version": f"0.2.4-test.{number}",
                    "tag": f"v0.2.4-test.{number}",
                    "notes": notes or "Novo izdanje Claw Metricsa.",
                    "asset_url": expected_url,
                    "sha256": match.group(1).lower(),
                    "release_url": f"https://github.com/{REPOSITORY}/releases/tag/v0.2.4-test.{number}",
                }
                best_number = number
                break
    return best


def check_github_update(package_file):
    current = installed_version(package_file)
    request = urllib.request.Request(
        RELEASES_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ClawMetrics-UpdateCheck/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise RuntimeError("GitHub odgovor je prevelik.")
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        raise RuntimeError("Nije moguće povezati se s GitHubom. Provjeri internet.") from error
    try:
        releases = json.loads(raw)
    except ValueError as error:
        raise RuntimeError("GitHub nije vratio valjane podatke o izdanjima.") from error
    candidate = latest_compatible_release(releases)
    return {
        "current": current,
        "available": bool(candidate and version_number(candidate["version"]) > version_number(current)),
        "latest": candidate,
    }
