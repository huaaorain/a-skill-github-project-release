# Release notes contract

Generate release notes from evidence:

- previous and current Git tags;
- commits and changed files between those tags;
- the previous release manifest, when available;
- tests and build results;
- user-visible documentation and screenshots;
- current artifact manifest.

Commit prefixes are hints, not proof. Verify a change against code, tests, or documentation before describing its user impact.

## Required content

Every release body must contain:

- a short summary of the release;
- new or changed user-facing capabilities;
- fixes and important internal changes;
- breaking changes or compatibility notes;
- upgrade or migration instructions, or an explicit statement that none are needed;
- supported platforms and important limitations;
- a per-file table generated from `release-manifest.json`;
- source commit and checksum guidance.

For the first public release, replace the comparison with an initial-release overview and explain the product's purpose, capabilities, supported platforms, and limitations.

## Localized release notes

When the user requests multiple languages in a Release body:

- Keep one complete source file per language under `docs/releases/`.
- Declare each file and anchor identifier under `release_notes.locales`.
- Use `layout: "accordion"` when only one language should be visible at a time. Each language becomes a `<details>` block, with exactly one block open by default.
- Use `layout: "anchors"` only when all languages should remain expanded and a top link menu jumps between sections.
- Keep the download/file table outside the language blocks and display it only once.
- Combine only useful description languages in the shared file table; do not repeat the entire table for every translation.
- Validate that every language contains the same version, compatibility facts, asset names, and source commit.

GitHub strips JavaScript and interactive CSS from README and Release Markdown. Collapsed `<details>` is the closest native alternative to tabs; true in-place tab switching requires a separate GitHub Pages site.

## File table

Use one row per distributed file:

| File | Role | Purpose | Size | SHA-256 |
| --- | --- | --- | ---: | --- |

Do not group several unrelated files under a vague "other files" description. GitHub's automatically generated source archives may be described separately and do not need checksum rows.

## Accuracy rules

- Never invent a feature from a file name.
- Never claim a fix unless the change or test supports it.
- Never hide a breaking data-format change.
- Name the previous version used for comparison.
- Mention when evidence was insufficient and request review rather than filling gaps.
- Keep versioned asset names and links identical across the README, manifest, and Release body.
