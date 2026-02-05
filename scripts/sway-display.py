#!/usr/bin/env python3
import json
import os
import subprocess as sb
import sys
from contextlib import suppress
from typing import Any, Generator
from pathlib import Path

LAPTOP = "eDP-1"
EXTERNAL = "DP-1"
LAPTOP_WIDTH = 1920


_BASE_DIR = Path(os.getenv("XDG_CACHE_HOME") or (Path.home() / ".cache"))
STATE_FILE = _BASE_DIR / "sway-display-state"


def get_external_screens() -> Generator[str]:
    cmd = ["swaymsg", "-t", "get_outputs"]
    res = sb.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError("Unable to run swaymsg")
    screens: list[dict[str, Any]] = json.loads(res.stdout)
    for scr in screens:
        name = scr["name"]
        if name != LAPTOP:
            yield name


def main():
    modes = ("mirror", "extend", "external", "laptop")

    action = "apply" if not sys.argv[1:] else sys.argv[1]

    current = "mirror"  # default state
    with suppress(FileNotFoundError), open(STATE_FILE) as f:
        content = f.read().strip()
        current = content if content else current

    next = current

    if action == "cycle":
        for i, mode in enumerate(modes):
            if mode == current:
                j = (i + 1) % len(modes)
                next = modes[j]
                break
        with open(STATE_FILE, "w") as f:
            f.write(next)

    mode = next

    res = "mode 1920x1080"
    l_cmd = f"enable {res} position 0 0"
    e_cmd = f"enable {res} position 0 0"

    match mode:
        case "extend":
            e_cmd = f"enable {res} position {LAPTOP_WIDTH} 0"
        case "external":
            l_cmd = "disable"
        case "laptop":
            e_cmd = "disable"
        case "mirror":
            """Do nothing"""
        case _:
            print("Unknown mode:", mode)
            exit(1)

    cmds = ["swaymsg", "-q"]
    arg = f"""\
    output {LAPTOP} {l_cmd}
    output {EXTERNAL} {e_cmd}
    """
    sb.run(cmds + [arg])


if __name__ == "__main__":
    main()
