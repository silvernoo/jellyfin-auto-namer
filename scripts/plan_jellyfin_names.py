#!/usr/bin/env python3
"""Plan or apply Jellyfin-friendly movie/show renames.

The script is intentionally conservative. It defaults to a dry run, preserves
extensions, keeps subtitle/audio sidecars aligned with videos, and reports
warnings when it cannot infer season/episode metadata.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


VIDEO_EXTS = {
    ".avi",
    ".divx",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".ogm",
    ".ogv",
    ".ts",
    ".webm",
    ".wmv",
}

SUBTITLE_EXTS = {".srt", ".ass", ".ssa", ".sub", ".vtt", ".idx", ".smi", ".sup"}
AUDIO_EXTS = {".aac", ".ac3", ".dts", ".eac3", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
SIDECAR_EXTS = SUBTITLE_EXTS | AUDIO_EXTS

IMAGE_NAMES = {
    "poster",
    "folder",
    "cover",
    "default",
    "movie",
    "show",
    "backdrop",
    "fanart",
    "background",
    "art",
    "banner",
    "logo",
    "clearlogo",
    "landscape",
    "thumb",
}

EXTRA_FOLDERS = {
    "behind the scenes",
    "deleted scenes",
    "interviews",
    "scenes",
    "samples",
    "shorts",
    "featurettes",
    "clips",
    "other",
    "extras",
    "trailers",
    "theme-music",
    "backdrops",
}

EXTRA_SUFFIXES = (
    "-trailer",
    ".trailer",
    "_trailer",
    " trailer",
    "-sample",
    ".sample",
    "_sample",
    " sample",
    "-scene",
    "-clip",
    "-interview",
    "-behindthescenes",
    "-deleted",
    "-deletedscene",
    "-featurette",
    "-short",
    "-other",
    "-extra",
)

RELEASE_TOKENS = {
    "2160p",
    "1080p",
    "720p",
    "480p",
    "uhd",
    "hdr",
    "hdr10",
    "dv",
    "remux",
    "bluray",
    "brrip",
    "bdrip",
    "webrip",
    "web-dl",
    "webdl",
    "hdtv",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "avc",
    "aac",
    "dts",
    "truehd",
    "atmos",
    "proper",
    "repack",
}

INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*]')
YEAR_RE = re.compile(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)")
PROVIDER_RE = re.compile(r"\[(tmdbid|imdbid|tvdbid)-([^\]]+)\]", re.IGNORECASE)
SEASON_DIR_RE = re.compile(r"^(?:season|s|se)\s*0*(\d{1,3})$", re.IGNORECASE)
SXXEYY_RE = re.compile(
    r"[Ss](?P<season>\d{1,3})\s*[._ -]?[Ee](?P<ep1>\d{1,3})(?:\s*(?:-|to|through|_)\s*[Ee]?(?P<ep2>\d{1,3}))?",
    re.IGNORECASE,
)
X_EP_RE = re.compile(r"(?P<season>\d{1,3})x(?P<ep1>\d{1,3})(?:\s*(?:-|to|through|_)\s*(?P<ep2>\d{1,3}))?", re.IGNORECASE)
EP_ONLY_RE = re.compile(r"(?:^|[ ._-])(?:ep?|episode)\s*0*(?P<ep1>\d{1,3})(?:\s*(?:-|to|through|_)\s*0*(?P<ep2>\d{1,3}))?", re.IGNORECASE)
PART_RE = re.compile(r"(?P<prefix>.*?)(?:[ ._-])(?P<parttype>cd|dvd|part|pt|disc|disk)[ ._-]?(?P<num>\d+|[a-d])$", re.IGNORECASE)
RESOLUTION_RE = re.compile(r"\b(2160p|1080p|720p|576p|480p|4k|uhd)\b", re.IGNORECASE)
THREED_RE = re.compile(r"(?:^|[ ._-])(3d[ ._-]?(?:hsbs|fsbs|htab|ftab|mvc))(?:$|[ ._-])", re.IGNORECASE)


@dataclass
class Operation:
    source: str
    target: str
    kind: str
    reason: str


@dataclass
class Plan:
    root: str
    library: str
    apply: bool
    operations: list[Operation]
    warnings: list[str]
    skipped: list[str]


def is_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTS


def is_sidecar(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SIDECAR_EXTS


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ._-")


def sanitize_component(value: str) -> str:
    value = value.replace(":", " - ")
    value = INVALID_CHARS_RE.sub(" ", value)
    value = normalize_spaces(value)
    return value.rstrip(".")


def humanize_title(value: str) -> str:
    value = re.sub(r"[._]+", " ", value)
    value = re.sub(r"\s+-\s+", " - ", value)
    value = normalize_spaces(value)
    if not value:
        return "Unknown Title"
    letters = re.sub(r"[^A-Za-z]", "", value)
    if letters and (letters.isupper() or letters.islower()):
        value = value.title()
        small_words = {"A", "An", "And", "As", "At", "But", "By", "For", "In", "Of", "On", "Or", "The", "To", "Vs"}
        parts = value.split()
        for idx in range(1, len(parts)):
            if parts[idx] in small_words:
                parts[idx] = parts[idx].lower()
        value = " ".join(parts)
    return sanitize_component(value)


def parse_providers(text: str) -> list[tuple[str, str]]:
    providers: list[tuple[str, str]] = []
    for provider, value in PROVIDER_RE.findall(text):
        normalized = provider.lower()
        item = (normalized, value.strip())
        if item not in providers:
            providers.append(item)
    return providers


def parse_provider_arg(raw: str) -> tuple[str, str]:
    value = raw.strip()
    bracket_match = PROVIDER_RE.fullmatch(value)
    if bracket_match:
        return bracket_match.group(1).lower(), bracket_match.group(2).strip()
    if "=" in value:
        provider, provider_value = value.split("=", 1)
    elif "-" in value:
        provider, provider_value = value.split("-", 1)
    else:
        raise ValueError(f"Provider must be like tmdbid=123, tvdbid=123, or imdbid=tt123: {raw}")
    provider = provider.lower().strip()
    provider_value = provider_value.strip()
    if provider not in {"tmdbid", "imdbid", "tvdbid"} or not provider_value:
        raise ValueError(f"Unsupported provider argument: {raw}")
    return provider, provider_value


def merge_providers(*provider_lists: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    for providers in provider_lists:
        for item in providers:
            normalized = (item[0].lower(), item[1].strip())
            if normalized not in merged:
                merged.append(normalized)
    order = {"tmdbid": 0, "tvdbid": 1, "imdbid": 2}
    return sorted(merged, key=lambda pair: (order.get(pair[0], 99), pair[0], pair[1]))


def format_provider_ids(providers: Iterable[tuple[str, str]]) -> str:
    return " ".join(f"[{provider}-{value}]" for provider, value in providers)


def infer_title_year(raw_name: str) -> tuple[str, str | None, list[tuple[str, str]]]:
    providers = parse_providers(raw_name)
    without_ids = PROVIDER_RE.sub(" ", raw_name)
    stem = Path(without_ids).stem
    stem = re.sub(r"[\[\](){}]", " ", stem)
    stem = re.sub(r"[._]+", " ", stem)
    year_match = YEAR_RE.search(stem)
    year = year_match.group(1) if year_match else None
    title_part = stem[: year_match.start()] if year_match else stem
    words = [word for word in normalize_spaces(title_part).split(" ") if word.lower() not in RELEASE_TOKENS]
    title = humanize_title(" ".join(words) if words else title_part)
    return title, year, providers


def format_media_name(title: str, year: str | None, providers: Iterable[tuple[str, str]]) -> str:
    base = sanitize_component(title)
    if year:
        base = f"{base} ({year})"
    ids = format_provider_ids(providers)
    if ids:
        base = f"{base} {ids}"
    return base


def find_video_files(folder: Path) -> list[Path]:
    return sorted([child for child in folder.iterdir() if is_video(child) and not is_extra_file(child)], key=lambda p: p.name.lower())


def find_sidecars(folder: Path) -> list[Path]:
    return sorted([child for child in folder.iterdir() if is_sidecar(child)], key=lambda p: p.name.lower())


def has_disc_folder(folder: Path) -> bool:
    return any(child.is_dir() and child.name.upper() in {"BDMV", "VIDEO_TS"} for child in folder.iterdir())


def is_extra_file(path: Path) -> bool:
    lowered_stem = path.stem.lower()
    if lowered_stem in {"trailer", "sample", "theme"}:
        return True
    return any(lowered_stem.endswith(suffix) for suffix in EXTRA_SUFFIXES)


def is_metadata_image(path: Path) -> bool:
    return path.is_file() and path.stem.lower() in IMAGE_NAMES


def detect_version_label(path: Path, index: int) -> str:
    stem = path.stem
    three_d = THREED_RE.search(stem)
    if three_d:
        return three_d.group(1).replace(".", "_").replace(" ", "_").upper()
    resolution = RESOLUTION_RE.search(stem)
    if resolution:
        value = resolution.group(1).lower()
        return "2160p" if value in {"4k", "uhd"} else value
    lowered = stem.lower()
    if "director" in lowered:
        return "Directors Cut"
    if "extended" in lowered:
        return "Extended Cut"
    if "theatrical" in lowered:
        return "Theatrical Cut"
    if "remux" in lowered:
        return "Remux"
    return f"Version {index:02d}"


def detect_part_suffix(stem: str) -> str | None:
    match = PART_RE.match(stem)
    if not match:
        return None
    return f"{match.group('parttype').lower()}{match.group('num').lower()}"


def same_path(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return str(a.absolute()).lower() == str(b.absolute()).lower()


def add_operation(operations: list[Operation], source: Path, target: Path, kind: str, reason: str) -> None:
    if same_path(source, target):
        return
    operations.append(Operation(str(source), str(target), kind, reason))


def add_sidecar_operations(
    operations: list[Operation],
    sidecars: Iterable[Path],
    old_stem: str,
    new_stem: str,
    reason: str,
    target_dir: Path | None = None,
) -> None:
    for sidecar in sidecars:
        if is_metadata_image(sidecar):
            continue
        if sidecar.stem == old_stem:
            suffix = ""
        elif sidecar.stem.startswith(old_stem + "."):
            suffix = sidecar.stem[len(old_stem) :]
        else:
            continue
        target_parent = target_dir if target_dir is not None else sidecar.parent
        target = target_parent / f"{new_stem}{suffix}{sidecar.suffix}"
        add_operation(operations, sidecar, target, "sidecar", reason)


def collect_metadata(path: Path, args: argparse.Namespace, single_item: bool) -> tuple[str, str | None, list[tuple[str, str]]]:
    inferred_title, inferred_year, inferred_providers = infer_title_year(path.name)
    arg_providers = [parse_provider_arg(raw) for raw in args.provider]
    title = sanitize_component(args.title) if args.title and single_item else inferred_title
    year = str(args.year) if args.year and single_item else inferred_year
    providers = merge_providers(arg_providers if single_item else [], inferred_providers)
    return title, year, providers


def plan_movie_item(path: Path, args: argparse.Namespace, single_item: bool, operations: list[Operation], warnings: list[str], skipped: list[str]) -> None:
    title, year, providers = collect_metadata(path, args, single_item)
    base_name = format_media_name(title, year, providers)

    if path.is_file():
        if not is_video(path):
            skipped.append(str(path))
            return
        movie_folder = path.parent / base_name
        target_video = movie_folder / f"{base_name}{path.suffix}"
        add_operation(operations, path, target_video, "video", "move loose movie file into its own Jellyfin movie folder")
        add_sidecar_operations(
            operations,
            find_sidecars(path.parent),
            path.stem,
            base_name,
            "move loose movie sidecar into movie folder",
            target_dir=movie_folder,
        )
        return

    if not path.is_dir():
        skipped.append(str(path))
        return

    videos = find_video_files(path)
    if not videos and not has_disc_folder(path):
        skipped.append(str(path))
        return

    target_folder = path.with_name(base_name)
    add_operation(operations, path, target_folder, "folder", "normalize movie folder name")

    if not videos:
        warnings.append(f"{path}: found disc folder but no top-level video files to rename")
        return

    sidecars = find_sidecars(path)
    if len(videos) == 1:
        video = videos[0]
        part_suffix = detect_part_suffix(video.stem)
        new_stem = f"{base_name}-{part_suffix}" if part_suffix else base_name
        add_operation(operations, video, video.with_name(f"{new_stem}{video.suffix}"), "video", "match movie video stem to movie folder")
        add_sidecar_operations(operations, sidecars, video.stem, new_stem, "match movie sidecar stem to video")
        return

    for index, video in enumerate(videos, start=1):
        part_suffix = detect_part_suffix(video.stem)
        if part_suffix:
            new_stem = f"{base_name}-{part_suffix}"
        else:
            label = detect_version_label(video, index)
            new_stem = f"{base_name} - {label}"
        add_operation(operations, video, video.with_name(f"{new_stem}{video.suffix}"), "video", "normalize movie version or part name")
        add_sidecar_operations(operations, sidecars, video.stem, new_stem, "match movie sidecar stem to video")


def parse_season_dir(path: Path) -> int | None:
    lowered = path.name.strip().lower()
    if lowered in {"special", "specials"}:
        return 0
    match = SEASON_DIR_RE.match(path.name.strip())
    if match:
        return int(match.group(1))
    return None


def target_season_folder(show_dir: Path, season_number: int) -> Path:
    return show_dir / f"Season {season_number:02d}"


def parse_episode(path: Path, fallback_season: int | None) -> tuple[int, int, int | None] | None:
    stem = path.stem
    for regex in (SXXEYY_RE, X_EP_RE):
        match = regex.search(stem)
        if match:
            return int(match.group("season")), int(match.group("ep1")), int(match.group("ep2")) if match.group("ep2") else None
    if fallback_season is not None:
        match = EP_ONLY_RE.search(stem)
        if match:
            return fallback_season, int(match.group("ep1")), int(match.group("ep2")) if match.group("ep2") else None
    return None


def episode_token(season: int, ep1: int, ep2: int | None) -> str:
    token = f"S{season:02d}E{ep1:02d}"
    if ep2 is not None:
        token = f"{token}-E{ep2:02d}"
    return token


def season_dirs(show_dir: Path) -> list[tuple[Path, int]]:
    found: list[tuple[Path, int]] = []
    for child in sorted([item for item in show_dir.iterdir() if item.is_dir()], key=lambda p: p.name.lower()):
        if child.name.lower() in EXTRA_FOLDERS:
            continue
        season_number = parse_season_dir(child)
        if season_number is not None:
            found.append((child, season_number))
    return found


def plan_episode_file(
    video: Path,
    season_number: int | None,
    show_dir: Path,
    series_label: str,
    operations: list[Operation],
    warnings: list[str],
) -> None:
    parsed = parse_episode(video, season_number)
    if not parsed:
        warnings.append(f"{video}: could not infer SxxEyy episode number; left unchanged")
        return
    parsed_season, ep1, ep2 = parsed
    token = episode_token(parsed_season, ep1, ep2)
    part_suffix = detect_part_suffix(video.stem)
    new_stem = f"{series_label} {token}"
    if part_suffix:
        new_stem = f"{new_stem}-{part_suffix}"
    target_parent = target_season_folder(show_dir, parsed_season)
    target = target_parent / f"{new_stem}{video.suffix}"
    add_operation(operations, video, target, "episode", "normalize show episode name and season folder")
    add_sidecar_operations(
        operations,
        find_sidecars(video.parent),
        video.stem,
        new_stem,
        "match episode sidecar stem to video",
        target_dir=target_parent,
    )


def plan_show_item(path: Path, args: argparse.Namespace, single_item: bool, operations: list[Operation], warnings: list[str], skipped: list[str]) -> None:
    if not path.is_dir():
        skipped.append(str(path))
        return

    title, year, providers = collect_metadata(path, args, single_item)
    show_folder_name = format_media_name(title, year, providers)
    series_label = sanitize_component(title)
    add_operation(operations, path, path.with_name(show_folder_name), "folder", "normalize show folder name")

    seasons = season_dirs(path)
    for season_dir, season_number in seasons:
        target = target_season_folder(path, season_number)
        add_operation(operations, season_dir, target, "folder", "normalize season folder name")
        for video in find_video_files(season_dir):
            plan_episode_file(video, season_number, path, series_label, operations, warnings)

    loose_videos = find_video_files(path)
    for video in loose_videos:
        plan_episode_file(video, None, path, series_label, operations, warnings)

    if not seasons and not loose_videos:
        skipped.append(str(path))


def choose_items(root: Path, library: str, item_mode: str, args: argparse.Namespace) -> tuple[list[Path], bool]:
    if item_mode == "root":
        return [root], True
    if item_mode == "children":
        children = sorted(root.iterdir(), key=lambda p: p.name.lower()) if root.is_dir() else [root]
        return children, False
    if args.title or args.year or args.provider:
        return [root], True
    if root.is_file():
        return [root], True
    if library == "show" and root.is_dir() and (season_dirs(root) or find_video_files(root)):
        return [root], True
    if library == "movie" and root.is_dir() and (find_video_files(root) or has_disc_folder(root)):
        return [root], True
    children = sorted(root.iterdir(), key=lambda p: p.name.lower()) if root.is_dir() else [root]
    return children, False


def validate_plan(operations: list[Operation], warnings: list[str]) -> None:
    targets_seen: dict[str, str] = {}
    for op in operations:
        source = Path(op.source)
        target = Path(op.target)
        if not source.exists():
            warnings.append(f"{source}: source no longer exists")
            continue
        target_key = str(target.absolute()).lower()
        if target_key in targets_seen and str(source.absolute()).lower() != targets_seen[target_key].lower():
            warnings.append(f"{target}: multiple sources target the same path")
        targets_seen[target_key] = str(source.absolute())
        if target.exists():
            try:
                same_existing = source.samefile(target)
            except OSError:
                same_existing = str(source.absolute()).lower() == str(target.absolute()).lower()
            if not same_existing:
                warnings.append(f"{target}: target already exists")


def finalize_operation_targets(operations: list[Operation]) -> list[Operation]:
    dir_moves = [
        (Path(op.source), Path(op.target))
        for op in sorted(operations, key=lambda item: len(Path(item.source).parts))
        if op.kind == "folder"
    ]
    finalized: list[Operation] = []
    for op in operations:
        target = rewrite_path(Path(op.target), dir_moves)
        finalized.append(Operation(op.source, str(target), op.kind, op.reason))
    return finalized


def build_plan(args: argparse.Namespace) -> Plan:
    root = Path(args.root).expanduser()
    operations: list[Operation] = []
    warnings: list[str] = []
    skipped: list[str] = []

    if not root.exists():
        raise FileNotFoundError(root)

    items, single_item = choose_items(root, args.library, args.item, args)
    if args.library == "movie":
        for item in items:
            plan_movie_item(item, args, single_item, operations, warnings, skipped)
    else:
        for item in items:
            plan_show_item(item, args, single_item, operations, warnings, skipped)

    if args.library == "movie":
        for provider in args.provider:
            parsed_provider, _ = parse_provider_arg(provider)
            if parsed_provider == "tvdbid":
                warnings.append("TVDB IDs are for shows only; do not add tvdbid to movie items unless you have a special reason")

    operations = finalize_operation_targets(operations)
    validate_plan(operations, warnings)
    return Plan(str(root), args.library, args.apply, operations, warnings, skipped)


def rewrite_path(path: Path, dir_moves: list[tuple[Path, Path]]) -> Path:
    rewritten = path
    for old, new in sorted(dir_moves, key=lambda move: -len(move[0].parts)):
        try:
            relative = rewritten.relative_to(old)
        except ValueError:
            continue
        rewritten = new / relative
    return rewritten


def rename_path(source: Path, target: Path) -> None:
    if same_path(source, target):
        return
    if not source.exists():
        raise FileNotFoundError(source)
    if target.exists():
        try:
            if not source.samefile(target):
                raise FileExistsError(target)
        except OSError:
            raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = source.with_name(f".{source.name}.jellyfin-tmp-{uuid.uuid4().hex}")
    source.rename(temp)
    temp.rename(target)


def apply_operations(operations: list[Operation]) -> None:
    dir_moves: list[tuple[Path, Path]] = []
    dir_ops = [op for op in operations if Path(op.source).is_dir()]
    file_ops = [op for op in operations if not Path(op.source).is_dir()]

    for op in sorted(dir_ops, key=lambda item: len(Path(item.source).parts)):
        source = rewrite_path(Path(op.source), dir_moves)
        target = rewrite_path(Path(op.target), dir_moves)
        rename_path(source, target)
        dir_moves.append((Path(op.source), Path(op.target)))

    for op in sorted(file_ops, key=lambda item: len(Path(item.source).parts)):
        source = rewrite_path(Path(op.source), dir_moves)
        target = rewrite_path(Path(op.target), dir_moves)
        rename_path(source, target)


def print_text_plan(plan: Plan) -> None:
    print(f"Root: {plan.root}")
    print(f"Library: {plan.library}")
    print(f"Mode: {'apply' if plan.apply else 'dry-run'}")
    print()
    if plan.operations:
        print("Operations:")
        for idx, op in enumerate(plan.operations, start=1):
            print(f"{idx:03d}. {op.kind}: {op.source}")
            print(f"     -> {op.target}")
            print(f"     {op.reason}")
    else:
        print("No rename operations planned.")
    if plan.warnings:
        print()
        print("Warnings:")
        for warning in plan.warnings:
            print(f"- {warning}")
    if plan.skipped:
        print()
        print("Skipped:")
        for item in plan.skipped:
            print(f"- {item}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Media file, item folder, or library root")
    parser.add_argument("--library", choices=["movie", "show"], required=True, help="Jellyfin library type")
    parser.add_argument("--item", choices=["auto", "root", "children"], default="auto", help="Treat root as one item, scan children, or infer")
    parser.add_argument("--title", help="Exact provider title for a single item")
    parser.add_argument("--year", type=int, help="Release or first-air year for a single item")
    parser.add_argument("--provider", action="append", default=[], help="Provider ID, e.g. tmdbid=569094, imdbid=tt9362722, tvdbid=266189")
    parser.add_argument("--apply", action="store_true", help="Apply the generated operations after validation")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        plan = build_plan(args)
        if args.apply and plan.warnings:
            print("Refusing to apply because warnings were found. Re-run without --apply, fix issues, then try again.", file=sys.stderr)
            if args.json:
                print(json.dumps(asdict(plan), indent=2, ensure_ascii=False))
            else:
                print_text_plan(plan)
            return 2
        if args.apply:
            apply_operations(plan.operations)
        if args.json:
            print(json.dumps(asdict(plan), indent=2, ensure_ascii=False))
        else:
            print_text_plan(plan)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
