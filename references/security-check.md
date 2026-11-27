# Pre-upload security check

Run the security check before `git add`, commit, push, and release creation. A secret that reaches any pushed commit must be treated as exposed even if a later commit deletes it.

## Commands

Full check against the release specification and declared artifacts:

```powershell
python "$SkillDir/scripts/release_manager.py" security-check --spec .github/release-spec.json
```

Source-only preliminary check before release artifacts exist:

```powershell
python "$SkillDir/scripts/release_manager.py" security-check --root .
```

Preflight runs the same full scan again before a Draft Release is accepted.

## Coverage

The helper checks:

- tracked, staged, and non-ignored untracked project files;
- common credential file names such as `.env`, private keys, token files, and credential stores;
- common GitHub, cloud, model-provider, payment, and private-key token formats;
- literal password, API-key, secret, and token assignments;
- ZIP release artifacts, including nested file names and UTF-8 text content;
- commits not present in a configured remote, using their patch history.

The output reports the file, archive entry, and finding category, but never prints the matched secret value.

`.env.example`, `.env.sample`, and `.env.template` are allowed only when they contain placeholders. Real credentials must stay outside the repository or in an ignored local file.

## Recommended `.gitignore`

```gitignore
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
*credential*
*secret*
*github-token*
release-build/
```

Adjust the list for the project, but do not weaken coverage for credentials that the application can create.

## Manual review

Automated scanning cannot prove a repository is secret-free. Also review screenshots, logs, generated reports, compiled binaries, ignored local data, and third-party configuration for:

- visible tokens, cookies, account identifiers, or personal paths;
- embedded application configuration or signing material;
- real user data in test fixtures, databases, archives, or model files;
- secrets in Git history or in files that GitHub Pages or an app bundle may publish.

## If a finding is real

1. Stop before commit, push, or upload.
2. Revoke or rotate the credential at its provider.
3. Replace it with an environment variable, ignored local file, or user-managed credential store.
4. If it was already pushed, treat it as compromised and coordinate repository-history cleanup separately; deleting only the current file is insufficient.
5. Never print the secret into a report, issue, chat, command line, or remote URL.
