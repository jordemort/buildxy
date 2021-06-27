import subprocess

from contextlib import contextmanager

CREATE_ARGS = [
    "--driver",
    "docker-container",
    "--buildkitd-flags",
    "--allow-insecure-entitlement security.insecure"
    + " --allow-insecure-entitlement network.host",
]


@contextmanager
def buildx_builder():
    builder = (
        subprocess.run(
            [
                "docker",
                "buildx",
                "create",
                *CREATE_ARGS,
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
