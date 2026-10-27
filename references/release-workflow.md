# Version release workflow

## Order of operations

Use this order so the tag, source commit, built artifacts, README, and release body describe the same version.

1. Determine the next version and verify that its tag and Release do not already exist. For a project with no published release, use `0.1.0` unless the user explicitly chooses another initial version.
2. Build and test from the intended source commit.
3. Capture or select real feature images and place them under `docs/assets/`.
4. Update README, installation instructions, compatibility notes, and the surface-level download information.
5. Create or update `.github/release-spec.json` with every release artifact, its role, description, required status, and stable download filename.
6. Update README and ensure `release-build/` is ignored.
7. Commit the source, documentation, screenshots, and release spec.
8. Push the branch and verify the remote commit.
9. From that exact commit, run `manifest`, `context`, `render-notes`, and `preflight`.
10. If preflight requires source changes, commit and push again, then regenerate the manifest.
11. Create and push an annotated tag on the manifest's commit.
12. Create a Draft Release with all assets.
13. Verify the draft and request approval to publish.
14. Publish, then regenerate the README's all-version catalog.
15. Review the catalog diff, commit only the generated catalog change, and push it.

## Artifact policy

Keep generated binaries out of Git. GitHub Release assets are individual files, so archive every required directory, such as a runtime folder or portable application directory.

Every release should include:

- versioned end-user artifacts;
- optional extension packs explicitly described as optional;
- `release-manifest.json`;
- `FILE_MANIFEST.md`;
- `SHA256SUMS.txt`;
- any license or third-party notice that the distributed files require.

Do not upload:

- source and debug caches;
- `bin/`, `obj/`, `node_modules/`, `.venv/`, or package-manager caches;
- personal reports, database files, user preferences, logs, or model caches;
- credentials, signing private keys, or files matched as secrets;
- preview or intermediate files that users cannot use.

GitHub generates source ZIP and TAR archives for each tag. Mention them as source downloads rather than uploading another source archive unless the project has a separate source bundle with a distinct purpose.

## Release notes

Use [release-notes-contract.md](release-notes-contract.md). The notes written for the GitHub Release and the notes summarized in README must agree. The file table generated from the release manifest is authoritative for asset names, descriptions, sizes, and checksums.

## Verification

Before publishing:

- all required artifacts exist and are regular files;
- no artifact is tracked by Git;
- no asset exceeds GitHub's per-file limit;
- every file has a useful description;
- each asset name is unique and stable enough for links;
- release notes have change, compatibility, and file sections;
- `SHA256SUMS.txt` matches the uploaded bytes;
- README contains at least one real feature image;
- README image and release links resolve;
- the Draft Release tag matches the intended commit.

If verification fails, fix the draft or local files. Do not delete an existing public release to make the command easier.

When only improving historical release documentation, use `update-release-notes`. It patches the release body and optional title while preserving the existing tag and every uploaded asset.
