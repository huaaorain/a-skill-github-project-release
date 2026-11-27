# Changelog

## [0.2.1] - 2026-11-27

### Added

- A `security-check` command that scans tracked, staged, untracked, outgoing
  Git-history, and ZIP artifact content for credential files and common token
  or password formats without printing matched values.
- Mandatory license-selection guidance covering common OSI licenses and
  source-available noncommercial alternatives.
- The project is now distributed under PolyForm Noncommercial License 1.0.0
  with a Required Notice attribution.

### Changed

- Preflight now runs the expanded security audit instead of checking only a
  small set of tracked-file token patterns.

## [0.2.0] - 2026-11-20

### Changed

- Preflight now requires `version_surfaces` and validates every declared
  current-version display, including README badges and text-based banner or
  screenshot files.
- README guidance now marks optional integrations and extensions with `*`
  while leaving required capabilities unstarred.
- The release-spec examples and initializer expose the new version-surface
  configuration.

### Fixed

- Corrected the skill banner's stale `v0.1.0` label and added automated checks
  so future banner, badge, and text-image versions must match the release tag.

## [0.1.2] - 2026-11-04

### Added

- Semantic icon guidance inspired by the feature presentation used in
  `linshenkx/prompt-optimizer`.
- A verified-advantages block in the README template using `✅` for
  evidence-backed capabilities.
- Stable explicit anchors for icon-prefixed headings used by README navigation.

### Changed

- Updated the template and all three localized project pages with consistent
  icons for features, installation, workflow, safety, downloads, and metadata.
- Clarified that icons should stay sparse and outside ordinary paragraphs,
  code, file paths, and tables.

## [0.1.1] - 2026-11-02

### Added

- Localized Release notes with configurable `accordion` and `anchors` layouts.
- Per-language release-note source files under `docs/releases/`.
- A shared bilingual file table generated once from the release manifest.
- Localized asset descriptions and preflight checks for language selectors,
  default-open content, filenames, and source metadata.

## [0.1.0] - 2026-10-27

### Added

- First public release of the A Skill: Github Project Release skill.
- First-publish workflow with a default initial version of `0.1.0`.
- Release-only artifact policy.
- Version manifests with file descriptions and SHA-256 checksums.
- Draft Release discovery, upload recovery, and validated publishing.
- README template with functional workflow imagery.
- Localized README catalogs and preflight validation.
- Release-note-only updates that preserve existing tags and assets.
- Offline smoke tests for manifests, catalogs, archives, preflight, and safety checks.
