from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .compiler import CompileConfig, CompileError, MAX_WORKERS_LIMIT, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile Mermaid diagrams into PDF files.")
    parser.add_argument("--src", type=Path, default=Path("mermaid"), help="Source directory with Mermaid files.")
    parser.add_argument("--dst", type=Path, default=Path("figures"), help="Output directory for generated PDFs.")
    parser.add_argument("--no-crop", action="store_true", help="Skip pdfcrop after mmdc generation.")
    parser.add_argument("--force", action="store_true", help="Rebuild all diagrams, even when PDFs are up to date.")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS_LIMIT,
        help=f"Maximum parallel workers. Default: {MAX_WORKERS_LIMIT}.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return run(
            CompileConfig(
                src=args.src,
                dst=args.dst,
                no_crop=args.no_crop,
                force=args.force,
                max_workers=args.max_workers,
            )
        )
    except CompileError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
