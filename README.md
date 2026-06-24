# Jellyfin Auto Namer

[中文](#中文) | [English](#english)

## 中文

### 项目简介

Jellyfin Auto Namer 是一个用于整理 Jellyfin 媒体库命名的 AI Agent 技能。

它可以帮助你按 Jellyfin 官方推荐的格式生成电影和剧集的重命名计划，让 Jellyfin 更容易识别影片、匹配元数据，并减少刮削失败的问题。

本项目适用于：

- 整理电影和剧集文件名
- 添加 TMDB、TVDB、IMDb 等 provider ID
- 规范 `Season 01`、`S01E01`、多集文件名
- 同步处理字幕、音轨等 sidecar 文件
- 在真正改名之前生成安全的 dry-run 计划

### 安装

#### 方法一：通过 npx 安装

```bash
npx skills add https://github.com/silvernoo/jellyfin-auto-namer.git
```

#### 方法二：通过 Git 克隆

```bash
git clone https://github.com/silvernoo/jellyfin-auto-namer.git ~/.codex/skills/jellyfin-auto-namer
```

Windows 用户可以克隆到：

```text
%USERPROFILE%\.codex\skills\jellyfin-auto-namer
```

#### 验证安装

重启或重新加载支持 skills 的客户端后，确认技能目录结构如下：

```text
jellyfin-auto-namer/
|-- SKILL.md
|-- README.md
|-- references/
|   `-- official-rules.md
`-- scripts/
    `-- plan_jellyfin_names.py
```

### 使用

#### 在 AI Agent 中使用

你可以这样对 Agent 说：

```text
请使用 jellyfin-auto-namer 技能检查这个媒体目录，并先生成 dry-run 重命名计划。
```

也可以指定媒体库类型：

```text
请用 jellyfin-auto-namer 整理 D:\Media\Movies，这是电影库。先不要实际改名。
```

#### 直接运行脚本

生成电影库重命名计划：

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie
```

生成剧集目录重命名计划：

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Shows/Series.Name.2021" --library show --title "Series Name" --year 2021 --provider tvdbid=12345
```

输出 JSON：

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie --json
```

确认计划无误后再执行实际改名：

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie --apply
```

### 命名示例

电影：

```text
Movies/
`-- Movie Name (2024) [tmdbid-12345]/
    `-- Movie Name (2024) [tmdbid-12345].mkv
```

剧集：

```text
Shows/
`-- Series Name (2021) [tvdbid-12345]/
    `-- Season 01/
        `-- Series Name S01E01.mkv
```

### 文件说明

- `SKILL.md` - 技能说明和 Agent 工作流程
- `references/official-rules.md` - Jellyfin 官方命名规则摘要
- `scripts/plan_jellyfin_names.py` - dry-run 重命名计划脚本
- `README.md` - 项目说明

### 参考资源

- [Jellyfin Movies](https://jellyfin.org/docs/general/server/media/movies/)
- [Jellyfin TV Shows](https://jellyfin.org/docs/general/server/media/shows/)
- [Jellyfin Metadata Provider Identifiers](https://jellyfin.org/docs/general/server/metadata/identifiers/)

### 说明

脚本默认只生成计划，不会修改文件。只有在添加 `--apply` 后才会执行重命名；如果发现警告，脚本会拒绝直接应用。

---

## English

### Overview

Jellyfin Auto Namer is an AI-agent skill for organizing Jellyfin media library names.

It helps generate Jellyfin-friendly rename plans for movies and TV shows, making files easier for Jellyfin to identify and match with metadata providers.

Use it to:

- Rename movie and TV show files
- Add TMDB, TVDB, and IMDb provider IDs
- Normalize `Season 01`, `S01E01`, and multi-episode names
- Keep subtitle and audio sidecar files aligned
- Generate a safe dry-run plan before changing files

### Installation

#### Option 1: Install with npx

```bash
npx skills add https://github.com/silvernoo/jellyfin-auto-namer.git
```

#### Option 2: Clone with Git

```bash
git clone https://github.com/silvernoo/jellyfin-auto-namer.git ~/.codex/skills/jellyfin-auto-namer
```

On Windows, clone it to:

```text
%USERPROFILE%\.codex\skills\jellyfin-auto-namer
```

#### Verify Installation

After restarting or reloading your skills-enabled client, the folder should look like this:

```text
jellyfin-auto-namer/
|-- SKILL.md
|-- README.md
|-- references/
|   `-- official-rules.md
`-- scripts/
    `-- plan_jellyfin_names.py
```

### Usage

#### Use With An AI Agent

Ask your agent:

```text
Use the jellyfin-auto-namer skill to inspect this media folder and create a dry-run rename plan first.
```

You can also specify the library type:

```text
Use jellyfin-auto-namer to organize D:\Media\Movies as a movie library. Do not rename files yet.
```

#### Run The Script Directly

Create a movie-library rename plan:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie
```

Create a show-folder rename plan:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Shows/Series.Name.2021" --library show --title "Series Name" --year 2021 --provider tvdbid=12345
```

Print JSON:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie --json
```

Apply changes only after reviewing the plan:

```bash
python scripts/plan_jellyfin_names.py "D:/Media/Movies" --library movie --apply
```

### Naming Examples

Movie:

```text
Movies/
`-- Movie Name (2024) [tmdbid-12345]/
    `-- Movie Name (2024) [tmdbid-12345].mkv
```

TV show:

```text
Shows/
`-- Series Name (2021) [tvdbid-12345]/
    `-- Season 01/
        `-- Series Name S01E01.mkv
```

### Files

- `SKILL.md` - Skill instructions and agent workflow
- `references/official-rules.md` - Summary of Jellyfin naming rules
- `scripts/plan_jellyfin_names.py` - Dry-run rename planner
- `README.md` - Project documentation

### References

- [Jellyfin Movies](https://jellyfin.org/docs/general/server/media/movies/)
- [Jellyfin TV Shows](https://jellyfin.org/docs/general/server/media/shows/)
- [Jellyfin Metadata Provider Identifiers](https://jellyfin.org/docs/general/server/metadata/identifiers/)

### Note

The script defaults to dry-run mode and does not modify files. It only renames files when `--apply` is provided, and it refuses to apply if warnings are found.
