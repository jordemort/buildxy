#!/usr/bin/env python3

import os
import re
import shlex
import subprocess
import sys

from contextlib import contextmanager
from typing import List

CONTAINER_NAME = os.environ.get("CONTAINER_NAME", None)
BUILDXY_MODE = os.environ.get("BUILDXY_MODE", "push")
PLATFORMS = os.environ.get("PLATFORMS", "linux/amd64")
CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "docker.io")
REGISTRY_USERNAME = os.environ.get("REGISTRY_USERNAME", None)
REGISTRY_PASSWORD = os.environ.get("REGISTRY_PASSWORD", None)
EXTRA_BUILD_ARGS = os.environ.get("EXTRA_BUILD_ARGS", None)
RAW_CONTAINER_TAG = os.environ.get(
    "CONTAINER_TAG",
    os.environ.get(
        "GITHUB_HEAD_REF",
        subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        .stdout.decode()
        .strip(),
    ),
)

CONTAINER_TAG = re.sub(r"[^a-zA-Z0-9]+", "-", RAW_CONTAINER_TAG)


def container_tag():
    if CONTAINER_TAG in ["main", "master"]:
        return "latest"
    else:
        return CONTAINER_TAG


def fatal_error(msg: str):
    sys.stderr.write(f"FATAL ERROR: {msg}\n")
    sys.exit(1)


def docker_login():
    if REGISTRY_USERNAME is None or REGISTRY_PASSWORD is None:
        return

    subprocess.run(
        [
            "docker",
            "login",
            CONTAINER_REGISTRY,
            "--username",
            REGISTRY_USERNAME,
            "--password-stdin",
        ],
        input=REGISTRY_PASSWORD,
        check=True,
    )


@contextmanager
def buildx_builder():
    builder = (
        subprocess.run(
            [
                "docker",
                "buildx",
                "create",
                "--driver",
                "docker-container",
                "--buildkitd-flags",
                "--allow-insecure-entitlement security.insecure"
                + " --allow-insecure-entitlement network.host",
                "--use",
            ],
            check=True,
            stdout=subprocess.PIPE,
        )
        .stdout.decode()
        .strip()
    )

    yield

    subprocess.run(["docker", "buildx", "rm", builder])


def main(argv: List[str] = sys.argv[1:]) -> int:
    if CONTAINER_NAME is None:
        fatal_error("CONTAINER_NAME is not set")

    docker_login()

    container_base = f"{CONTAINER_REGISTRY}/{CONTAINER_NAME}"
    container_name = f"{container_base}:{container_tag()}"
    latest_cache = f"{container_base}:latest.cache"
    my_cache = f"{container_name}.cache"

    buildx = [
        "docker",
        "buildx",
        "build",
        "--tag",
        container_name,
        "--pull",
        "--load",
        "--platform",
        PLATFORMS,
        "--cache-from",
        my_cache,
    ]

    if my_cache != latest_cache:
        buildx += ["--cache-from", latest_cache]

    if BUILDXY_MODE == "push":
        buildx += ["--cache-to", f"type=registry,ref={my_cache},mode=max"]

    if EXTRA_BUILD_ARGS is not None:
        buildx += shlex.split(EXTRA_BUILD_ARGS)

    buildx += argv

    with buildx_builder():
        subprocess.run(buildx, check=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
