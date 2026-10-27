# Changelog

## [1.0.2] - 2026-10-27

### Fixed

- Download Draft Release metadata through the authenticated Release Asset API.
- Verify publish-time asset sizes without relying on temporary `untagged-*`
  browser download URLs.

## [1.0.1] - 2026-10-27

### Internal draft

- Find authenticated Draft Releases through the release list instead of the
  by-tag endpoint, which does not return drafts.
- Added an offline regression test for draft discovery.

This draft was superseded by `1.0.2` after Draft asset retrieval was corrected.

## [1.0.0] - 2026-10-27

### Internal draft

- First public release of the GitHub Project Release skill.
- First-publish workflow for new GitHub repositories.
- Release-only artifact policy.
- Version manifests with file descriptions and SHA-256 checksums.
- Draft Release creation, upload recovery, and verified publishing.
- README template with functional workflow imagery.
- Localized README catalog generation and preflight validation.
- Release-note-only updates that preserve existing tags and assets.
- Offline smoke tests for manifests, catalogs, archives, preflight, and safety checks.

This draft was superseded by `1.0.1` after draft-release discovery was corrected.
