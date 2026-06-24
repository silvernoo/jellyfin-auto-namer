---
name: jellyfin-auto-namer
description: Plan and apply Jellyfin-friendly movie and TV show names so metadata scraping works reliably. Use when an AI agent needs to rename or organize media files/folders for Jellyfin, fix failed movie or show identification, add TMDB/TVDB/IMDB provider IDs, normalize Season folders, SxxEyy episode names, movie version labels, external subtitle/audio sidecars, extras, or generate a safe dry-run rename plan for media directories.
---

# Jellyfin Auto Namer

## Goal

Produce safe Jellyfin-friendly movie and TV show paths that are easy for Jellyfin's metadata scanners to identify. Prefer official provider titles, release year, and provider IDs over release-scene names or guessed titles.

Always create and review a dry-run plan before changing files. Apply a plan only when the user explicitly asks for renaming or accepts the proposed changes.

## Required Reference

Read `references/official-rules.md` before answering rule questions, creating a rename plan, or applying any rename. It summarizes the relevant official Jellyfin docs and links the source pages.

## Workflow

1. Inspect the media tree with `rg --files`, `Get-ChildItem`, or equivalent.
2. Determine the Jellyfin library type: `movie` or `show`. Avoid mixed movie/show libraries; Jellyfin's docs call that library type broken and deprecated.
3. Collect exact metadata:
   - Movie: provider title, release year, optional `[tmdbid-...]` and/or `[imdbid-...]`.
   - Show: provider title, first-air year, optional `[tmdbid-...]`, `[tvdbid-...]`, and/or `[imdbid-...]`.
4. If metadata is uncertain and web access is available, verify against the metadata provider or a reliable source. If you infer from filenames only, state that confidence is lower.
5. Generate a dry-run plan with `scripts/plan_jellyfin_names.py`.
6. Review warnings, collisions, low-confidence names, sidecar moves, and any files the script skipped.
7. Apply only after the user has requested actual renaming or approved the plan.

## Naming Targets

Use these target forms unless the user has a strong existing convention that still matches Jellyfin's rules.

Movies:

```txt
Movies/
|-- Movie Name (2024) [tmdbid-12345] [imdbid-tt1234567]/
    |-- Movie Name (2024) [tmdbid-12345] [imdbid-tt1234567].mkv
```

Movie versions:

```txt
Movie Name (2024) [tmdbid-12345]/
|-- Movie Name (2024) [tmdbid-12345] - 2160p.mkv
|-- Movie Name (2024) [tmdbid-12345] - 1080p.mkv
|-- Movie Name (2024) [tmdbid-12345] - Directors Cut.mkv
```

Shows:

```txt
Shows/
|-- Series Name (2021) [tvdbid-12345]/
    |-- Season 00/
    |   |-- Series Name S00E01.mkv
    |-- Season 01/
        |-- Series Name S01E01.mkv
        |-- Series Name S01E02-E03.mkv
```

External subtitles and audio sidecars must keep the same base name as the video, then append language and flags:

```txt
Movie Name (2024).mkv
Movie Name (2024).en.forced.srt
Series Name S01E01.ja.ass
```

## Script Usage

Run the script from the skill directory. It uses only the Python standard library.

Dry-run a movie library:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie
```

Dry-run one known movie item:

```bash
python scripts/plan_jellyfin_names.py "D:/Downloads/Spider.Man.Across.the.Spider-Verse.2023.1080p.mkv" --library movie --title "Spider-Man: Across the Spider-Verse" --year 2023 --provider tmdbid=569094 --provider imdbid=tt9362722
```

Dry-run a show:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Shows/Series.Name.2021" --library show --title "Series Name" --year 2021 --provider tvdbid=12345
```

Emit machine-readable output:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Shows" --library show --json
```

Apply a reviewed plan:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie --apply
```

## Safety Rules

- Preserve extensions exactly.
- Preserve and rename sidecar subtitles/audio when they share the old video stem.
- Do not rename metadata images (`poster.jpg`, `folder.jpg`, `cover.png`, `backdrop.jpg`, `logo.png`) as videos.
- Do not collapse multi-episode files unless the user asks to split media with another tool.
- Do not invent provider IDs. Use IDs supplied by the user or verified from provider pages.
- Do not use filesystem-reserved or Jellyfin-problematic characters in path components: `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`.
- Convert provider-title colons to ` - ` in filenames, because `:` is not portable on Windows and is listed as problematic by Jellyfin.
- Report skipped files and unresolved episodes instead of guessing aggressively.
