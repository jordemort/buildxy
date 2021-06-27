import json
import subprocess

from typing import Any, Dict, Optional


def container_diff(tag: str, type: str) -> Optional[Dict[str, Any]]:
    try:
        raw = subprocess.run(
            [
                "container-diff",
                "diff",
                "--json",
                "--type",
                type,
                f"remote://{tag}",
                f"daemon://{tag}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode()

        return json.loads(raw)[0]
    except subprocess.CalledProcessError:
        return None


def container_changed(tag: str) -> bool:
    metadata_diff = container_diff(tag, "metadata")
    if metadata_diff is None:
        return True

    if len(metadata_diff["Diff"]["Adds"]) > 0:
        return True

    if len(metadata_diff["Diff"]["Dels"]) > 0:
        return True

    file_diff = container_diff(tag, "file")
    if file_diff is None:
        return True

    if len(file_diff["Diff"]["Adds"]) > 0:
        return True

    if len(file_diff["Diff"]["Dels"]) > 0:
        return True

    if len(file_diff["Diff"]["Mods"]) > 0:
        return True

    return False
