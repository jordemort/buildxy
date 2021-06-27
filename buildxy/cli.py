import sys

from typing import List

from buildxy.buildx import buildx


def main(argv: List[str] = sys.argv[1:]) -> int:
    try:
        result = buildx(argv)
    except Exception as e:
        sys.stderr.write(f"ERROR - {e.__class__.__name__}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
