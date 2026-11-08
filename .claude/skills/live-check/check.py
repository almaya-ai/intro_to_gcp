#!/usr/bin/env python3
"""Check the live service and bucket. Exit 0 only if every check passes.

Settings come from .env in the current folder (copy env.example) or the environment.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED = ("PROJECT", "SERVICE", "BUCKET_NAME", "SERVICE_URL")
FOOTER = re.compile(r"generation (\d+) · revision ([\w-]+)")

failures = 0


def load_settings():
    settings = dict(os.environ)
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator and not name.startswith("#"):
                settings[name.strip()] = value.strip()
    missing = [name for name in REQUIRED if not settings.get(name)]
    if missing:
        print(f"Missing settings: {', '.join(missing)}. Copy env.example to .env and fill it in.", file=sys.stderr)
        sys.exit(2)
    return settings


def report(ok, name, detail=""):
    global failures
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.status, response.headers, response.read().decode()
    except urllib.error.HTTPError as err:
        return err.code, err.headers, err.read().decode(errors="replace")


def gcloud(project, *args):
    result = subprocess.run(
        ["gcloud", *args, "--project", project, "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def check_page(url, expect_text, expect_revision):
    status, headers, body = fetch(url + "/")
    report(status == 200, "page returns 200", str(status))
    report(headers.get("Cache-Control") == "no-store", "page is never cached", str(headers.get("Cache-Control")))
    footer = FOOTER.search(body)
    report(bool(footer), "page shows generation and revision")
    if footer:
        print(f"      generation={footer[1]} revision={footer[2]}")
    if expect_text:
        report(expect_text in body, f"page shows '{expect_text}'")
    if expect_revision:
        report(bool(footer) and footer[2] == expect_revision, f"revision is {expect_revision}", footer[2] if footer else "none")


def check_failure_states(url):
    status, _, _ = fetch(url + "/?file=live-check-missing.txt")
    report(status == 404, "missing file returns 404", str(status))
    status, _, _ = fetch(url + "/?file=..%2Fx.txt")
    report(status == 400, "unsafe file name returns 400", str(status))


def check_privacy(project, bucket_name):
    status, _, _ = fetch(f"https://storage.googleapis.com/{bucket_name}/message.txt")
    report(status in (401, 403), "anonymous bucket access is blocked", str(status))
    bucket = gcloud(project, "storage", "buckets", "describe", f"gs://{bucket_name}")
    report(bucket.get("public_access_prevention") == "enforced", "public access prevention is enforced")
    report(bucket.get("uniform_bucket_level_access") is True, "uniform bucket access is on")


def check_identity(project, service, bucket_name):
    member = f"serviceAccount:{service}@{project}.iam.gserviceaccount.com"
    policy = gcloud(project, "storage", "buckets", "get-iam-policy", f"gs://{bucket_name}")
    roles = [b["role"] for b in policy["bindings"] if member in b["members"]]
    report(roles == ["roles/storage.objectViewer"], "service account is objectViewer on the bucket", ",".join(roles))
    policy = gcloud(project, "projects", "get-iam-policy", project)
    roles = [b["role"] for b in policy["bindings"] if member in b["members"]]
    report(not roles, "service account has no project-level role", ",".join(roles))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-text")
    parser.add_argument("--expect-revision")
    args = parser.parse_args()
    settings = load_settings()
    project, service, bucket_name = settings["PROJECT"], settings["SERVICE"], settings["BUCKET_NAME"]
    url = settings["SERVICE_URL"].rstrip("/")
    check_page(url, args.expect_text, args.expect_revision)
    check_failure_states(url)
    check_privacy(project, bucket_name)
    check_identity(project, service, bucket_name)
    print(f"\n{failures} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
