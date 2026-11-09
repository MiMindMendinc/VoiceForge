"""Command line entry point for VoiceForge.

    voiceforge serve             start the server; downloads missing model files first
    voiceforge serve --no-download
    voiceforge download [--check | --force]

Automatic download on `serve` is skipped when any of these is set:
  --no-download, VOICEFORGE_NO_DOWNLOAD=1, CI=true (set by GitHub Actions).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping

TRUTHY = frozenset({"1", "true", "yes", "on"})


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY


def download_blocked(environ: Mapping[str, str] | None = None, no_download_flag: bool = False) -> str | None:
    """Return why automatic model download is disabled, or None if it is allowed."""
    env = os.environ if environ is None else environ
    if no_download_flag:
        return "--no-download was given"
    if _truthy(env.get("VOICEFORGE_NO_DOWNLOAD")):
        return "VOICEFORGE_NO_DOWNLOAD is set"
    if _truthy(env.get("CI")):
        return "CI is set"
    return None


def ensure_models(model_dir, missing: list[str], blocked: str | None) -> int:
    """Download missing model files unless blocked. Returns a process exit code."""
    if not missing:
        return 0
    if blocked:
        print(f"Model files missing ({', '.join(missing)}); not downloading because {blocked}.")
        return 0
    import download_models

    print(f"Model files missing in {model_dir}; downloading them now (about 350 MB).")
    return download_models.main(["--dir", str(model_dir)])


def _serve(args: argparse.Namespace) -> int:
    import server
    from tts.engine import TTSEngine

    try:
        settings = server.Settings.from_env()
    except server.SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    missing = TTSEngine(settings.model_dir).missing_files()
    code = ensure_models(settings.model_dir, missing, download_blocked(no_download_flag=args.no_download))
    if code != 0:
        print("Model download failed; starting without speech.", file=sys.stderr)
    server.main()
    return 0


def _download(args: argparse.Namespace) -> int:
    import download_models

    argv = []
    if args.dir:
        argv += ["--dir", args.dir]
    if args.check:
        argv.append("--check")
    if args.force:
        argv.append("--force")
    return download_models.main(argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voiceforge", description="Local text-to-speech server.")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="start the HTTP server (configure with VOICEFORGE_* env vars)")
    serve.add_argument("--no-download", action="store_true", help="never download missing model files")
    serve.set_defaults(func=_serve)

    dl = sub.add_parser("download", help="download and verify the model files")
    dl.add_argument("--dir", help="folder for the model files (default: ./models)")
    mode = dl.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="only verify existing files")
    mode.add_argument("--force", action="store_true", help="download again even if files verify")
    dl.set_defaults(func=_download)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
