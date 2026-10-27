---
name: github-project-release
description: Publish a finished project to GitHub or an existing repository, build versioned release assets, generate a screenshot-based project README, and maintain release notes and download catalogs. Use for first-time GitHub uploads, new releases, or release documentation refreshes; not for unrelated Git maintenance.
---

# GitHub Project Release

Publish source code to Git, keep executables and distributable extensions in GitHub Releases, and leave the repository with a complete project page and version archive.

## Required policy

- Keep source, build files, documentation, and small authored assets in Git.
- Keep executables, archives, runtimes, installers, model packs, and other generated distributables out of Git. Upload them only as Release assets. Do not weaken this policy unless the user explicitly changes it.
- Never commit secrets, personal data, local reports, API tokens, model caches, or build intermediates.
- Prefer a Draft Release. Creating a repository, pushing commits, changing repository visibility, publishing a release, and changing an existing tag are external mutations: obtain fresh user authorization immediately before each category of action.
- Never force-push, move a published tag, overwrite a release, or delete a release asset to recover from a failure.
- Never present generated artwork as a real product screenshot. Use real UI/CLI captures or clearly labeled diagrams.

## Inputs

Use the repository's current files, Git state, build system, existing release history, and `.github/release-spec.json`. If the spec does not exist, initialize it from [assets/release-spec.example.json](assets/release-spec.example.json).

Authentication for GitHub API operations comes from `GITHUB_TOKEN` or `GH_TOKEN`. Never print the token, place it in a remote URL, or write it into a project file. Mutating repository operations normally need repository Contents write access; first-time repository creation also needs permission to create repositories in the target account or organization.

`SKILL_DIR` below means the absolute directory containing this `SKILL.md`. In PowerShell, set it before running helpers:

```powershell
$SkillDir = "C:\path\to\github-project-release"
python "$SkillDir\scripts\release_manager.py" --help
```

When the project is on another shell, use the equivalent path expansion.

## Workflow

### 1. Classify the task

- Read [references/first-publish.md](references/first-publish.md) when the project has no GitHub repository yet.
- Read [references/release-workflow.md](references/release-workflow.md) for every new version or release documentation refresh.
- Read [references/media-and-screenshots.md](references/media-and-screenshots.md) before collecting the functional images.
- Read [references/release-notes-contract.md](references/release-notes-contract.md) before writing change summaries.
- For README structure and content, read [references/readme-template.md](references/readme-template.md) and start from [assets/README.template.md](assets/README.template.md).

### 2. Inspect and build

Detect the project type and supported platforms, run its tests and production build, and identify the exact user-facing artifacts. Build from the same commit that will be tagged. Do not describe commands or features that the project cannot demonstrate.

Use `$SkillDir/scripts/release_manager.py archive` when a release artifact must be represented by a directory archive. Never upload a directory directly; GitHub Release assets are files.

### 3. Establish repository and version context

For an existing remote:

```powershell
python "$SkillDir/scripts/release_manager.py" repo-info --repo OWNER/REPO
python "$SkillDir/scripts/release_manager.py" context --spec .github/release-spec.json --tag v1.2.0
```

For a first upload, follow the confirmation and git setup sequence in `references/first-publish.md`.

The version must be unambiguous before editing release files. Prefer Semantic Versioning unless the project already uses a different scheme. Reject an existing tag or release instead of reusing or moving it.

### 4. Prepare project documents

Build a real feature introduction with at least one local image under `docs/assets/`. Explain what is visible and tie every image to a real feature, workflow, interface, or architecture component.

Update the README with real installation steps, the latest downloads, a screenshot-led feature overview, and the generated release catalog markers. Add `release-build/` to `.gitignore`; it contains generated manifests, notes, and staged artifacts. Use the README template as a content checklist, not as generic boilerplate.

When multiple languages are requested, create a complete README for each language, add a compact switcher below the badges, and declare every file under `readme.locales`. Keep the same screenshots, download URLs, section order, and catalog markers across translations.

Write the human summary later from `release-context.json`, project documentation, tests, and diffs. Do not commit generated `release-build/` files.

### 5. Commit before measuring the release

Commit the final source, `.github/release-spec.json`, README, screenshots, and build changes. Push the branch and verify that the remote commit is the intended source state.

Generate the artifact inventory from that pushed commit:

```powershell
python "$SkillDir/scripts/release_manager.py" manifest --spec .github/release-spec.json --tag v1.2.0 --output release-build
```

Build release context and write the human-readable summary:

```powershell
python "$SkillDir/scripts/release_manager.py" context --spec .github/release-spec.json --tag v1.2.0
```

Then render the release body:

```powershell
python "$SkillDir/scripts/release_manager.py" render-notes --spec .github/release-spec.json --tag v1.2.0 --summary release-build/summary.md --manifest release-build/release-manifest.json --output release-build/release-notes.md
```

Run preflight after committing:

```powershell
python "$SkillDir/scripts/release_manager.py" preflight --spec .github/release-spec.json --tag v1.2.0 --notes release-build/release-notes.md
```

Preflight now validates tracked source and the committed release artifacts. If it requires source changes, make a new commit, push, and regenerate the manifest before tagging.

### 6. Tag and create the Draft Release

Create an annotated tag on the exact commit recorded in `release-manifest.json`, then push the tag. Create a Draft Release and upload every artifact plus the three metadata files:

```powershell
python "$SkillDir/scripts/release_manager.py" create-release --spec .github/release-spec.json --tag v1.2.0 --target COMMIT_SHA --notes release-build/release-notes.md --assets release-build/target.zip release-build/release-manifest.json release-build/FILE_MANIFEST.md release-build/SHA256SUMS.txt
```

Verify:

- The Draft Release points to the intended tag and commit.
- Every required asset is present exactly once.
- Sizes and SHA-256 values match.
- Release notes include change summary, compatibility notes, and a per-file table.
- README image paths and release links resolve.

After explicit approval, publish:

```powershell
python "$SkillDir/scripts/release_manager.py" publish-release --repo OWNER/REPO --tag v1.2.0 --confirm
```

To improve the notes of an already published release without changing its assets or tag:

```powershell
python "$SkillDir/scripts/release_manager.py" update-release-notes --repo OWNER/REPO --tag v1.2.0 --notes release-build/release-notes.md --confirm
```

### 7. Refresh the all-version catalog

```powershell
python "$SkillDir/scripts/release_manager.py" catalog --spec .github/release-spec.json --write
```

This replaces only the marked release-catalog block in README with every published version and its asset links. Verify that `git diff` changes only that block, then commit and push the catalog refresh. If the project also publishes elsewhere, the README may optionally add a pointer to an automated workflow, but the skill's release-time catalog update remains the fallback.

```powershell
git diff -- README.md
git add README.md
git commit -m "docs: update release catalog for v1.2.0"
git push
```

## Failure handling

- Build, test, secret, or preflight failure: stop before committing or tagging.
- Authentication or permission failure: report the missing capability; do not search for or expose credentials.
- Release creation succeeds but an asset upload fails: leave the draft in place, report which asset failed, and resume with `upload-assets` after fixing the problem.
- README catalog refresh fails: keep the release published and report the unrefreshed catalog; do not alter or republish the release.
- Existing tag or release: stop and require an explicitly chosen new version.

## Helper reference

Run `python "$SkillDir/scripts/release_manager.py" --help` for the supported deterministic operations. The helper uses Python's standard library and Git/GitHub APIs; it does not require GitHub CLI.
