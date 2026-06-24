# Jellyfin Naming Rules Reference

This file summarizes the official Jellyfin docs used by this skill. Re-check the live docs if exact current behavior matters.

Sources:

- Movies: https://jellyfin.org/docs/general/server/media/movies/
- TV Shows: https://jellyfin.org/docs/general/server/media/shows/
- Mixed Movies and Shows: https://jellyfin.org/docs/general/server/media/mixed-movies-and-shows/
- Metadata Provider Identifiers: https://jellyfin.org/docs/general/server/metadata/identifiers/

## General Video Rules

- Use the correct Jellyfin library type: `Movies` for movies, `Shows` for TV series.
- Avoid `Mixed Movies and Shows`; Jellyfin's docs describe it as broken and deprecated.
- Match the name used by the metadata provider whenever possible.
- Avoid these problematic filename characters: `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`.
- On Windows-compatible libraries, replace title colons with ` - `, e.g. `Spider-Man: Across the Spider-Verse` becomes `Spider-Man - Across the Spider-Verse`.
- Common video containers such as `.mp4` and `.mkv` are supported.
- `VIDEO_TS` and `BDMV` folders are supported for movies and music videos, but not for multiple versions, multiple parts, or external subtitle/audio tracks.
- Disc images such as `.iso` may work but are not supported; Jellyfin recommends remuxing to `.mkv` or extracting to `VIDEO_TS`/`BDMV`.

## Metadata Provider IDs

Provider IDs improve matching and may be placed in movie/show folder or file names.

Format:

```txt
Movie Name (year) [metadata provider id]
Series Name (year) [metadata provider id]
```

Examples:

```txt
Best Movie Ever (1994) [tmdbid-680] [imdbid-tt0111161]
Series Name (2018) [tvdbid-79168]
Spider-Man - Across the Spider-Verse (2023) [tmdbid-569094] [imdbid-tt9362722]
```

Supported providers listed by Jellyfin:

- TMDB: `[tmdbid-569094]`
- TVDB: `[tvdbid-266189]` for shows only
- OMDb/IMDb IDs: `[imdbid-tt9362722]`

## Movies

Use one folder per movie. The movie folder name should be:

```txt
Movie Name (year) [metadata provider id]
```

The `year` and metadata provider IDs are optional, but help Jellyfin match correctly. The video file inside the folder should have the same base name as the folder, optionally with supported tags.

Target:

```txt
Movies/
|-- Movie Name (2024) [tmdbid-12345]/
    |-- Movie Name (2024) [tmdbid-12345].mkv
    |-- Movie Name (2024) [tmdbid-12345].en.forced.srt
```

Multiple movie versions must begin exactly with the parent folder name, then ` - ` and a label. The hyphen form is required for automatic grouping.

```txt
Movie Name (2024) [tmdbid-12345]/
|-- Movie Name (2024) [tmdbid-12345] - 2160p.mkv
|-- Movie Name (2024) [tmdbid-12345] - 1080p.mkv
|-- Movie Name (2024) [tmdbid-12345] - Directors Cut.mkv
```

Multipart movies can be stacked with supported part tokens such as `cd`, `dvd`, `part`, `pt`, `disc`, or `disk`:

```txt
Movie Name (2010)/
|-- Movie Name (2010)-cd1.mkv
|-- Movie Name (2010)-cd2.mkv
```

Multipart does not work with multiple versions or manual version merging.

## TV Shows

Use series folders, then season folders, then episode files.

Series folder:

```txt
Series Name (year) [metadata provider id]
```

Season folders must be named `Season *`, not `S01` or `SE01`. Pad numbers for stable sorting:

```txt
Season 00
Season 01
Season 02
```

Episodes should include an `SxxEyy` token. Multi-episode files may use a range, but splitting into individual episodes gives better metadata.

```txt
Shows/
|-- Series Name (2021) [tvdbid-12345]/
    |-- Season 00/
    |   |-- Series Name S00E01.mkv
    |-- Season 01/
        |-- Series Name S01E01.mkv
        |-- Series Name S01E02-E03.mkv
```

Do not mix season folders and episode files directly under the show folder. Move loose episode files into the correct `Season NN` folder.

Specials belong in `Season 00`. If a provider does not identify a special, prefer a descriptive filename rather than a guessed `S00Exx` number.

## External Subtitles And Audio

External subtitle/audio files can be added with suffixes after the exact video base name:

```txt
Movie Name (2024).mkv
Movie Name (2024).default.en.forced.ass
Movie Name (2024).en.sdh.srt
Series Name S01E01.ja.ass
Series Name S01E01.commentary.ja.aac
```

Known flags include:

- Default: `default`
- Forced: `forced`, `foreign`
- Hearing impaired: `sdh`, `cc`, `hi`

## Extras And Theme Media

Supported extras folders include:

```txt
behind the scenes
deleted scenes
interviews
scenes
samples
shorts
featurettes
clips
other
extras
trailers
theme-music
backdrops
```

Single-file extras may use names such as `trailer.ext` or `sample.ext`, or suffixes such as `-trailer`, `.trailer`, `_trailer`, `-sample`, `-interview`, `-behindthescenes`, `-deletedscene`, `-featurette`, `-short`, `-other`, and `-extra`.

Theme media:

- Theme song: `theme.ext` or files under `theme-music/`
- Theme video: files under `backdrops/`

## 3D Tags

3D files use a `3D` tag plus one format tag, separated by space, hyphen, dot, or underscore. Supported format tags include:

- `hsbs`
- `fsbs`
- `htab`
- `ftab`
- `mvc`

Examples:

```txt
Movie Name (2024).3D.FTAB.mkv
Series Name S01E01.3d.hsbs.mkv
Movie Name (2024) - 3D_FTAB.mkv
```
