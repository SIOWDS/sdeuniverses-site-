#!/usr/bin/env python3
"""Build Frontier panels 581--592 with the shared V7 renderer."""
from __future__ import annotations

import argparse
from pathlib import Path

import build_frontier_541_550 as base

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tools" / "frontier_581_592_data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("numbers", nargs="*", type=int)
    args = parser.parse_args()
    numbers = args.numbers or list(range(581, 593))
    for number in numbers:
        matches = list(DATA.glob(f"{number}-*.json"))
        if len(matches) != 1:
            raise SystemExit(f"data for {number}: {matches}")
        base.build(matches[0])


if __name__ == "__main__":
    main()
