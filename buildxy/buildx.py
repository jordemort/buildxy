import os
import shlex
import shutil
import subprocess

from dataclasses import dataclass
from pathlib import Path

from buildxy.builder import buildx_builder
from buildxy.diff import container_changed
from buildxy.push import PushMode, should_push
from buildxy.tag import container_tag

EXTRA_BUILD_ARGS = os.environ.get("EXTRA_BUILD_ARGS", None)
CACHE = Path(
    os.environ.get("BUILDXY_CACHE", Path(os.getcwd()).joinpath(".buildxy-cache"))
).absolute()


@dataclass
class BuildxyResult:
    name: str
    pushed: bool


def buildx(*args: str) -> BuildxyResult:
    container_name = os.environ.get("CONTAINER_NAME", None)
    if container_name is None:
        raise ValueError("CONTAINER_NAME is not set")

    if shutil.which("docker") is None:
        raise RuntimeError("docker not found in PATH")

    if shutil.which("container-diff") is None:
        raise RuntimeError("contianer-diff not found in PATH")

    container_tagged = f"{container_name}/{container_tag()}"
    cache_to = CACHE.with_suffix(".new")

    build_args = [
        "docker",
        "buildx",
        "build",
        "--tag",
        container_tagged,
        "--pull",
        "--load",
        "--cache-from",
        f"type=local,src={str(CACHE)}",
        "--cache-to",
        f"type=local,dest={str(cache_to)},mode=max",
    ]

    if EXTRA_BUILD_ARGS is not None:
        build_args += shlex.split(EXTRA_BUILD_ARGS)

    if len(args) > 0:
        build_args += args
    else:
        build_args.append(".")

    with buildx_builder():
        subprocess.run(build_args, check=True)

    push_mode = should_push()
    if push_mode == PushMode.NEVER:
        return BuildxyResult(container_tagged, False)

    if push_mode == PushMode.CHANGED:
        if not container_changed(container_tagged):
            return BuildxyResult(container_tagged, False)

    subprocess.run(["docker", "push", container_tagged], check=True)
    return BuildxyResult(container_tagged, True)
