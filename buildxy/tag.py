import os
import re
import subprocess


def raw_tag():
    if "CONTAINER_TAG" in os.environ:
        return os.environ["CONTAINER_TAG"]
    elif "GITHUB_HEAD_REF" in os.environ:
        return os.environ["GITHUB_HEAD_REF"]

    return (
        subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        .stdout.decode()
        .strip()
    )


def clean_tag():
    return re.sub(r"[^a-zA-Z0-9]+", "-", raw_tag())


def container_tag():
    clean = clean_tag()

    if clean in ["main", "master"]:
        return "latest"
    else:
        return clean
