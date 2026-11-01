"""Updater safety tests: never install arbitrary URLs or skip checksum checks."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import updates


def release(n, *, digest=None, draft=False, url=None):
    tag=f"v0.2.4-test.{n}"
    filename=f"ClawMetrics-{tag}.zip"
    asset=f"https://github.com/ikorljan-droid/claw-metrics/releases/download/{tag}/{filename}"
    return {
        "draft": draft, "tag_name": tag,
        "body": f"Promjene za {tag} - zadržane postavke i renderer.",
        "assets": [{
            "name": filename, "browser_download_url": url or asset,
            "digest": digest if digest is not None else "sha256:" + "a"*64,
            "size": 3048697,
        }],
    }


class UpdateChecks(unittest.TestCase):
    def test_installed_version_is_taken_from_packaged_json(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"package.json"
            path.write_text(json.dumps({"version":"0.2.4-test.40"}))
            self.assertEqual(updates.installed_version(path),"0.2.4-test.40")
            path.write_text(json.dumps({"version":"not a release"}))
            with self.assertRaisesRegex(RuntimeError, "podržanom formatu"):
                updates.installed_version(path)

    def test_versions_compare_numerically_not_lexically(self):
        self.assertEqual(updates.version_number("v0.2.4-test.100"),100)
        self.assertEqual(updates.version_number("0.2.4-test.9"),9)
        self.assertIsNone(updates.version_number("v0.2.4-test.99-evil"))
        self.assertIsNone(updates.version_number("0.2.5-test.3"))

    def test_latest_release_from_prerelease_list_is_safe_and_sorted(self):
        source=[release(39),release(41),release(42,draft=True),
                release(40),release(43,digest=""),release(44,url="https://bad.invalid/pkg.zip"),
                release(45,digest="sha256:bad"), release(38)]
        newest=updates.latest_compatible_release(source)
        self.assertEqual(newest["tag"],"v0.2.4-test.41")
        self.assertEqual(newest["sha256"],"a"*64)
        self.assertEqual(newest["version"],"0.2.4-test.41")
        self.assertTrue(newest["asset_url"].startswith("https://github.com/ikorljan-droid/claw-metrics/releases/download/"))
        self.assertNotIn("bad.invalid",newest["asset_url"])

    def test_ignores_other_project_and_unsafe_or_incomplete_archives(self):
        for candidate in [
            {"tag_name":"v0.2.4-test.60","assets":[{"name":"xx.zip"}]},
            release(60,url="https://github.com/other/thing/releases/download/t/xx.zip"),
            release(60,digest=""),
            release(60,draft=True),
            {**release(60),"tag_name":"v0.2.4-test.60-rc"},
        ]:
            self.assertIsNone(updates.latest_compatible_release([candidate]))

    def test_success_github_api_and_exact_digest(self):
        with tempfile.TemporaryDirectory() as d:
            package=Path(d)/"package.json"
            package.write_text('{"version":"0.2.4-test.40"}')
            data=json.dumps([release(39),release(41)]).encode()
            with patch.object(updates.urllib.request,"urlopen",return_value=io.BytesIO(data)) as fetch:
                info=updates.check_github_update(package)
            self.assertEqual(info["current"],"0.2.4-test.40")
            self.assertTrue(info["available"])
            self.assertEqual(info["latest"]["version"],"0.2.4-test.41")
            self.assertEqual(info["latest"]["sha256"],"a"*64)
            url=fetch.call_args.args[0]
            self.assertEqual(url.full_url,updates.RELEASES_API)
            self.assertEqual(fetch.call_args.kwargs["timeout"],10)

    def test_offline_or_old_git_hub_release_does_not_offer_update(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"package.json"
            path.write_text('{"version":"0.2.4-test.40"}')
            with patch.object(updates.urllib.request,"urlopen",
                return_value=io.BytesIO(json.dumps([release(39),release(40)]).encode())):
                self.assertFalse(updates.check_github_update(path)["available"])
            with patch.object(updates.urllib.request,"urlopen",side_effect=OSError("offline")):
                with self.assertRaisesRegex(RuntimeError,"povezati"):
                    updates.check_github_update(path)

    def test_rejects_oversized_api_payloads_and_untrusted_release_body(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"package.json"
            path.write_text('{"version":"0.2.4-test.40"}')
            with patch.object(updates.urllib.request,"urlopen",
                return_value=io.BytesIO(b"x"*(updates.MAX_RESPONSE+5))):
                with self.assertRaisesRegex(RuntimeError,"prevelik"):
                    updates.check_github_update(path)
            item=release(41)
            item["body"]="X"*9000
            info=updates.latest_compatible_release([item])
            self.assertEqual(len(info["notes"]),5000)


if __name__=="__main__":
    unittest.main()
