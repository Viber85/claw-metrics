"""Manual GitHub Releases update discovery for Claw Metrics.

The privileged plugin backend only reads release metadata. It never extracts or
installs ZIPs: installation is delegated to Decky Loader's own confirmation
and SHA-256-verifying installer. The updater accepts numbered test releases
and Frame Gen release candidates with exact official GitHub asset URLs.
"""
import json
import pathlib
import re
import urllib.error
import urllib.request

REPOSITORY = "Viber85/claw-metrics"
RC_PATTERN = re.compile(r"^v?0\.3\.0-rc\.([1-9][0-9]{0,5})$")
RELEASES_API = "https://api.github.com/repos/" + REPOSITORY + "/releases?per_page=30"
VERSION_PATTERN = re.compile(r"^v?0\.2\.4-test\.(\d+)$")
SHA256_PATTERN = re.compile(r"^sha256:([a-fA-F0-9]{64})$")
MAX_RESPONSE = 2 * 1024 * 1024
MAX_ASSET_BYTES = 30 * 1024 * 1024


def version_number(value):
    if not isinstance(value, str):
        return None
    match = VERSION_PATTERN.fullmatch(value)
    if match:
        return (0, int(match.group(1)))
    match = RC_PATTERN.fullmatch(value)
    return (1, int(match.group(1))) if match else None


def installed_version(package_file):
    try:
        data = json.loads(pathlib.Path(package_file).read_text(encoding="utf-8"))
        value = data.get("version")
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError("Unable to read installed plugin version.") from error
    if version_number(value) is None:
        raise RuntimeError("Installed version has an unsupported format.")
    return value


def latest_compatible_release(releases):
    best = None
    best_number = (-1, 0)
    if not isinstance(releases, list):
        raise RuntimeError("GitHub did not return a list of releases.")
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        number = version_number(tag)
        if number is None or number <= best_number:
            continue
        version = tag.removeprefix("v")
        file_name = f"ClawMetrics-v{version}.zip"
        expected_url = (
            f"https://github.com/{REPOSITORY}/releases/download/"
            f"v{version}/{file_name}"
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
                    "version": version,
                    "tag": f"v{version}",
                    "notes": notes or "Novo izdanje Claw Metricsa.",
                    "asset_url": expected_url,
                    "sha256": match.group(1).lower(),
                    "release_url": f"https://github.com/{REPOSITORY}/releases/tag/v{version}",
                }
                best_number = number
                break
    return best


def validate_github_feed(package_file, raw):
    """Validate release JSON received by the Decky Loader HTTPS client.

    Do not trust the frontend with release links: only canonical GitHub assets
    and real release SHA-256 hashes may reach the update confirmation screen.
    """
    current = installed_version(package_file)
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_RESPONSE:
        raise RuntimeError("Invalid or oversized GitHub response.")
    try:
        releases = json.loads(raw)
    except ValueError as error:
        raise RuntimeError("GitHub returned invalid release data.") from error
    candidate = latest_compatible_release(releases)
    return {
        "current": current,
        "available": bool(candidate and version_number(candidate["version"]) > version_number(current)),
        "latest": candidate,
    }


def describe_error(error):
    """User-safe diagnostic returned as RPC data, never a Python exception."""
    if isinstance(error, urllib.error.HTTPError):
        code = error.code
        if code in (403, 429):
            return f"GitHub rate limit reached (HTTP {code}). Try again later."
        return f"GitHub API returned HTTP {code}."
    message = str(error).strip() or "Unknown error"
    if isinstance(error, urllib.error.URLError):
        reason = getattr(error, "reason", None)
        message = str(reason or error)
    # Avoid exposing arbitrary paths, URLs or entire HTTP responses in QAM.
    return type(error).__name__ + ": " + message[:260]


def check_github_update(package_file):
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
        raise RuntimeError("Unable to reach GitHub. Check network access or authentication.") from error
    return validate_github_feed(package_file, raw.decode("utf-8"))
