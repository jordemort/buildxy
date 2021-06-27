import os

from enum import Enum


class PushMode(Enum):
    CHANGED = 1
    ALWAYS = 2
    NEVER = 3


def should_push():
    push = os.environ.get("BUILDXY_PUSH", None)
    if push is None:
        return PushMode.CHANGED

    push = push.strip().lower()

    if push in ["changed", "t", "true", "y", "yes", "1"]:
        return PushMode.CHANGED
    elif push == "always":
        return PushMode.ALWAYS
    elif push in ["n", "no", "never", "f", "false", "0"]:
        return PushMode.NEVER

    raise ValueError(f"Unknown value for BUILDXY_PUSH: {push}")
