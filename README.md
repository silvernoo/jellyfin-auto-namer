# Jellyfin TMDB Skills

[中文](#中文) | [English](#english)

## 中文

一个面向通用 AI Agent 的 Jellyfin 媒体库自动命名技能包。它把 Jellyfin 官方媒体命名规则整理成可复用的说明、参考资料和脚本，帮助 Agent 或用户为电影和剧集生成更容易被 Jellyfin 正确识别、刮削和匹配元数据的文件夹名与文件名。

当前包含：

- `jellyfin-auto-namer`：Jellyfin 电影/剧集命名技能，包含规则说明、官方规则摘要和安全的 dry-run 重命名计划脚本。

目录结构：

```text
jellyfin-auto-namer/
|-- SKILL.md
|-- references/
|   |-- official-rules.md
|-- scripts/
    |-- plan_jellyfin_names.py
```

### 功能

- 电影命名：`Movie Name (year) [tmdbid-...] [imdbid-...]`
- 剧集命名：`Series Name (year) [tvdbid-...] / Season 01 / Series Name S01E01.mkv`
- 支持 TMDB、TVDB、IMDB provider ID
- 规范化 `Season 01`、`S01E01`、多集 `S01E02-E03`
- 处理电影多版本：`Movie Name (year) - 2160p.mkv`
- 保留并同步重命名字幕/音轨 sidecar 文件
- 默认 dry-run，只输出计划，不直接修改媒体库
- 避免 Jellyfin 和 Windows 不友好的路径字符

### 给 AI Agent 使用

让你的 Agent 读取：

- `jellyfin-auto-namer/SKILL.md`
- `jellyfin-auto-namer/references/official-rules.md`

建议提示词：

```text
Use the Jellyfin auto-naming skill in ./jellyfin-auto-namer to inspect this media folder, verify metadata when needed, and produce a safe dry-run rename plan before applying any changes.
```

### 直接运行脚本

生成电影库重命名计划：

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie
```

生成单个剧集目录重命名计划：

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Shows\Series.Name.2021" --library show --title "Series Name" --year 2021 --provider tvdbid=12345
```

确认计划后再执行：

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie --apply
```

输出 JSON：

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie --json
```

### Jellyfin 官方规则摘要

- 电影建议一部电影一个文件夹，视频文件名与父文件夹同名。
- 剧集建议使用剧集文件夹、`Season NN` 文件夹和 `SxxEyy` 文件名。
- 年份和 provider ID 可选，但能显著提高匹配准确率。
- Jellyfin 官方不推荐使用 `Mixed Movies and Shows` library type。

参考：

- [Jellyfin Movies](https://jellyfin.org/docs/general/server/media/movies/)
- [Jellyfin TV Shows](https://jellyfin.org/docs/general/server/media/shows/)
- [Jellyfin Metadata Provider Identifiers](https://jellyfin.org/docs/general/server/metadata/identifiers/)

## English

A Jellyfin media auto-naming skill package for general-purpose AI agents. It packages Jellyfin's official media organization rules into reusable instructions, references, and scripts so agents or users can create movie and TV show paths that are easier for Jellyfin to identify, scrape, and match with metadata providers.

Included:

- `jellyfin-auto-namer`: a Jellyfin movie/TV naming skill with rules, official-rule references, and a safe dry-run rename planner.

Structure:

```text
jellyfin-auto-namer/
|-- SKILL.md
|-- references/
|   |-- official-rules.md
|-- scripts/
    |-- plan_jellyfin_names.py
```

### Features

- Movie naming: `Movie Name (year) [tmdbid-...] [imdbid-...]`
- TV naming: `Series Name (year) [tvdbid-...] / Season 01 / Series Name S01E01.mkv`
- TMDB, TVDB, and IMDB provider IDs
- Normalizes `Season 01`, `S01E01`, and multi-episode `S01E02-E03` names
- Handles movie versions such as `Movie Name (year) - 2160p.mkv`
- Preserves and renames subtitle/audio sidecar files with matching video stems
- Dry-run by default, so media libraries are not modified without confirmation
- Avoids path characters that are problematic for Jellyfin and Windows

### Use With AI Agents

Point your agent at:

- `jellyfin-auto-namer/SKILL.md`
- `jellyfin-auto-namer/references/official-rules.md`

Suggested prompt:

```text
Use the Jellyfin auto-naming skill in ./jellyfin-auto-namer to inspect this media folder, verify metadata when needed, and produce a safe dry-run rename plan before applying any changes.
```

### Run The Planner Directly

Generate a movie-library rename plan:

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie
```

Generate a single show-folder rename plan:

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Shows\Series.Name.2021" --library show --title "Series Name" --year 2021 --provider tvdbid=12345
```

Apply only after reviewing the plan:

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie --apply
```

Emit JSON:

```powershell
python .\jellyfin-auto-namer\scripts\plan_jellyfin_names.py "D:\Media\Movies" --library movie --json
```

### Jellyfin Rule Summary

- Movies should generally use one folder per movie, with the video file matching the parent folder name.
- TV shows should use a series folder, `Season NN` folders, and `SxxEyy` episode filenames.
- Year and provider IDs are optional but improve matching accuracy.
- Jellyfin's official docs do not recommend the `Mixed Movies and Shows` library type.

References:

- [Jellyfin Movies](https://jellyfin.org/docs/general/server/media/movies/)
- [Jellyfin TV Shows](https://jellyfin.org/docs/general/server/media/shows/)
- [Jellyfin Metadata Provider Identifiers](https://jellyfin.org/docs/general/server/metadata/identifiers/)
