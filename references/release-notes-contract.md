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
