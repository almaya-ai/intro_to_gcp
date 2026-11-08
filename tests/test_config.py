"""Configuration stays documented and out of the code, and real env files stay out of git.

Scripts run here against a fake gcloud, so a test can never touch real cloud resources.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "env.example"
CHECK = ROOT / ".claude" / "skills" / "live-check" / "check.py"
SETTINGS = ("PROJECT", "REGION", "SERVICE", "BUCKET_NAME", "SERVICE_URL")


def is_git_ignored(name):
    result = subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT)
    return result.returncode == 0


def documented_names():
    text = EXAMPLE.read_text(encoding="utf-8")
    return set(re.findall(r"^#?\s*([A-Z_]+)=", text, flags=re.M))


@pytest.fixture
def sandbox(tmp_path):
    """A working folder without .env, and a PATH whose gcloud records any call and fails."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "gcloud-calls"
    fake = bin_dir / "gcloud"
    fake.write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\nexit 99\n')
    fake.chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()
    return work, {"PATH": f"{bin_dir}:{os.environ['PATH']}"}, calls


def test_every_env_var_the_service_reads_is_documented():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    names = set(re.findall(r'os\.environ(?:\.get\(|\[)"(\w+)"', source))
    assert names, "expected main.py to read environment variables"
    assert names <= documented_names()


def test_every_deployment_setting_is_documented():
    assert set(SETTINGS) <= documented_names()


def test_example_values_are_placeholders():
    text = EXAMPLE.read_text(encoding="utf-8")
    assert "PROJECT=your-project-id" in text
    assert "BUCKET_NAME=your-unique-bucket-name" in text


@pytest.mark.parametrize("name", ["PROJECT", "REGION", "SERVICE", "BUCKET_NAME"])
def test_deploy_stops_before_any_cloud_call_without_its_settings(sandbox, name):
    work, env, calls = sandbox
    env |= {key: "x" for key in SETTINGS if key != name}
    result = subprocess.run(
        ["bash", str(ROOT / "deploy.sh")], cwd=work, env=env, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert name in result.stderr
    assert not calls.exists()


def test_live_check_stops_before_any_cloud_call_without_its_settings(sandbox):
    work, env, calls = sandbox
    result = subprocess.run(
        [sys.executable, str(CHECK)], cwd=work, env=env, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "PROJECT" in result.stderr
    assert "Traceback" not in result.stderr
    assert not calls.exists()


def test_example_file_is_tracked_by_git():
    assert not is_git_ignored("env.example")


@pytest.mark.parametrize("name", [".env", ".env.local", ".env.production"])
def test_real_env_files_are_ignored_by_git(name):
    assert is_git_ignored(name)
