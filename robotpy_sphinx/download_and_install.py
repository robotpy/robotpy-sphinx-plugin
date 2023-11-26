#!/usr/bin/env python3
#
# Downloads an artifact from github actions and installs it. Tuned for what
# our pipeline generates -- artifacts contain wheels that are uploaded before
# RTD is pinged to do a build
#
# This exists because pypi takes way too long to guarantee that a build is
# available, and because building our artifacts on readthedocs would take
# too long.
#

import argparse
import fnmatch
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import typing
import zipfile

import packaging.tags
import packaging.utils
import requests


class DownloadError(Exception):
    pass


sys_tags = list(packaging.tags.sys_tags())


def is_wheel_compatible(whl_fname: str) -> bool:
    _, _, _, whl_tags = packaging.utils.parse_wheel_filename(whl_fname)
    for sys_tag in sys_tags:
        for whl_tag in whl_tags:
            if sys_tag == whl_tag:
                return True
    return False


def download_artifact_wheel(
    token: str,
    owner: str,
    repo: str,
    gh_branch_or_tag: str,
    head_sha: str,
    run_name: str,
    artifact_name: str,
    whl_path: pathlib.Path,
) -> typing.List[pathlib.Path]:
    s = requests.session()
    s.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-Github-Api-Version": "2022-11-28",
        }
    )

    print(
        "Getting workflow runs for",
        f"{owner}/{repo}",
        f"branch={gh_branch_or_tag} head_sha={head_sha}",
    )

    # Get the runs for the specified SHA
    r = s.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/runs?event=push&branch={gh_branch_or_tag}&head_sha={head_sha}"
    )

    # identify by the name if there's more than one
    runs = r.json()["workflow_runs"]
    if len(runs) == 0:
        raise DownloadError(f"{head_sha} not found for {gh_branch_or_tag}")
    for run in runs:
        if run["name"] == run_name:
            break
    else:
        raise DownloadError(
            f"{run_name} not found in {head_sha} for {gh_branch_or_tag}"
        )

    # Find the artifacts for this run
    print("Getting artifacts list from", run["artifacts_url"])
    for artifact in s.get(run["artifacts_url"]).json()["artifacts"]:
        if artifact["name"] == artifact_name:
            break
    else:
        raise DownloadError(f"artifact '{artifact_name}' not found")

    print("Downloading zipfile from", artifact["archive_download_url"])
    artifact_content = s.get(artifact["archive_download_url"])
    artifact_content_fp = io.BytesIO(artifact_content.content)

    # extract a wheel matching this python
    wheels: typing.List[pathlib.Path] = []
    with zipfile.ZipFile(artifact_content_fp) as zfp:
        for zf in zfp.infolist():
            if fnmatch.fnmatch(zf.filename, "*.whl"):
                print(".. checking", zf.filename)
                if "/" in zf.filename or ".." in zf.filename or "\\" in zf.filename:
                    raise DownloadError("invalid filename!")
                if is_wheel_compatible(zf.filename):
                    print("   -> is compatible!")
                    out_fname = whl_path / zf.filename
                    with open(out_fname, "wb") as wfp:
                        with zfp.open(zf) as zwfp:
                            wfp.write(zwfp.read())
                    wheels.append(out_fname)
    if not wheels:
        raise DownloadError(f"Could not find compatible wheel")

    return wheels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("default_branch")
    parser.add_argument("run_name")
    parser.add_argument("artifact_name")
    args = parser.parse_args()

    token = os.environ["GITHUB_API_TOKEN"]

    # Get the current revision
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    # figure out the branch -- either the default branch, or if this has been tagged
    # then the tag name
    try:
        gh_branch = subprocess.check_output(
            ["git", "describe", "--exact-match", "--tags"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        gh_branch = args.default_branch

    with tempfile.TemporaryDirectory() as tmp:
        try:
            wheels = download_artifact_wheel(
                token,
                args.owner,
                args.repo,
                gh_branch,
                head_sha,
                args.run_name,
                args.artifact_name,
                pathlib.Path(tmp),
            )
        except DownloadError as e:
            print("ERROR:", e, file=sys.stderr)
            exit(1)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "--disable-pip-version-check",
                "install",
            ]
            + list(map(str, wheels))
        )
        exit(proc.returncode)


if __name__ == "__main__":
    main()
