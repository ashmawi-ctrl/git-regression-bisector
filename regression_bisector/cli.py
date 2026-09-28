import argparse
from pathlib import Path

from .git import GitError
from .runner import BisectError, bisect_first_bad


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-regression-bisector",
        description=(
            "Find the first commit that turns a verification command "
            "from passing to failing."
        ),
    )
    parser.add_argument("repo", type=Path)
    parser.add_argument("--good", required=True)
    parser.add_argument("--bad", required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Verification command, normally supplied after --.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = tuple(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("error: provide a verification command after --")
        return 2

    try:
        result = bisect_first_bad(
            args.repo,
            good_ref=args.good,
            bad_ref=args.bad,
            command=command,
            timeout_seconds=args.timeout,
        )
    except (BisectError, GitError, ValueError) as exc:
        print(f"error: {exc}")
        return 2

    print(f"first bad commit: {result.first_bad_commit}")
    print(f"probes: {len(result.probes)}")
    for probe in result.probes:
        state = "pass" if probe.passed else "fail"
        if probe.timed_out:
            state = "timeout"
        print(
            f"- {probe.commit[:12]} {state} "
            f"exit={probe.exit_code} "
            f"duration={probe.duration_seconds:.3f}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
