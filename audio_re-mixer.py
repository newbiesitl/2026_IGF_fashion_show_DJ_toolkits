#!/usr/bin/env python3
"""
Remix a source audio file by concatenating configured segments.

YAML config fields:
  source_file: path to input audio (e.g. audios/the_mission.mp3)
  output_file: path for the mixed output (e.g. outputs/the_mission_remixed.mp3)
  session_configs: list of segments to append in order
    - start: segment start time in seconds
    - end: segment end time in seconds
    - fade_in: fade-in duration in milliseconds
    - fade_out: fade-out duration in milliseconds

Total output length is the sum of (end - start) for each session.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which

import imageio_ffmpeg
import yaml


def ffmpeg_executable() -> str:
    return which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(path: Path, base: Path) -> Path:
    return path if path.is_absolute() else base / path


def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"ffmpeg failed:\n{detail}")


def extract_segment(
    ffmpeg: str,
    source: Path,
    output: Path,
    start_sec: float,
    end_sec: float,
    fade_in_ms: int,
    fade_out_ms: int,
) -> None:
    duration = end_sec - start_sec
    filters: list[str] = []
    if fade_in_ms > 0:
        filters.append(f"afade=t=in:st=0:d={fade_in_ms / 1000:.3f}")
    if fade_out_ms > 0:
        fade_out_start = max(0.0, duration - fade_out_ms / 1000)
        filters.append(
            f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_ms / 1000:.3f}"
        )

    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration:.3f}",
    ]
    if filters:
        cmd.extend(["-af", ",".join(filters)])
    cmd.append(str(output))
    run_ffmpeg(cmd)


def concat_segments(ffmpeg: str, segment_paths: list[Path], output: Path) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    ) as manifest:
        for path in segment_paths:
            escaped = str(path).replace("'", "'\\''")
            manifest.write(f"file '{escaped}'\n")
        manifest_path = Path(manifest.name)

    try:
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest_path),
            "-c",
            "copy",
            str(output),
        ]
        try:
            run_ffmpeg(cmd)
        except RuntimeError:
            # Re-encode when stream formats differ (e.g. mixed extensions).
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                str(output),
            ]
            run_ffmpeg(cmd)
    finally:
        manifest_path.unlink(missing_ok=True)


def remix(config: dict, config_path: Path, ffmpeg: str) -> Path:
    base = config_path.parent
    source_path = resolve_path(Path(config["source_file"]), base)
    output_path = resolve_path(Path(config["output_file"]), base)

    if not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    sessions = config.get("session_configs") or []
    if not sessions:
        raise ValueError("session_configs must contain at least one segment")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix or ".mp3"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        segment_paths: list[Path] = []

        for index, session in enumerate(sessions, start=1):
            start = float(session["start"])
            end = float(session["end"])
            if end <= start:
                raise ValueError(
                    f"session_configs[{index}]: end ({end}) must be greater than start ({start})"
                )

            fade_in = int(session.get("fade_in", 0))
            fade_out = int(session.get("fade_out", 0))
            segment_path = tmp_dir / f"segment_{index:03d}{suffix}"
            extract_segment(
                ffmpeg, source_path, segment_path, start, end, fade_in, fade_out
            )
            segment_paths.append(segment_path)

        concat_segments(ffmpeg, segment_paths, output_path)

    return output_path


def total_duration_seconds(config: dict) -> float:
    return sum(
        float(s["end"]) - float(s["start"]) for s in config["session_configs"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Concatenate audio segments from a YAML remix config."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config (e.g. the_mission.yaml)",
    )
    args = parser.parse_args()

    if not args.config.is_file():
        sys.exit(f"Config file not found: {args.config}")

    config = load_config(args.config)
    if "output_file" not in config:
        sys.exit("Config must include output_file")

    try:
        output_path = remix(config, args.config, ffmpeg_executable())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        sys.exit(str(exc))

    duration = total_duration_seconds(config)
    segment_count = len(config["session_configs"])
    print(
        f"Wrote {output_path} ({duration:.1f}s expected, "
        f"{segment_count} segment(s))"
    )


if __name__ == "__main__":
    main()
