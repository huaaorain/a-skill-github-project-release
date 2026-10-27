# First GitHub publish

Use this flow only when no target GitHub repository exists.

## Preconditions

1. Inspect the project without assuming its stack. Run its tests and a production build.
2. Confirm the project has an appropriate `.gitignore`, README, license status, and no secrets or personal runtime data.
3. Confirm the repository owner, name, visibility, description, homepage, and topics with the user.
4. Confirm that executables and distributable extensions will be Release assets, not Git files.
5. Start the first public release at `0.1.0` unless the user explicitly chooses another initial version. Never assume `1.0.0`.
6. Initialize `.github/release-spec.json` if needed:

   ```powershell
   python "$SkillDir/scripts/release_manager.py" init --root PROJECT_ROOT --repo OWNER/REPO
   ```

## Create and push

Create the remote only after authorization:

```powershell
python "$SkillDir/scripts/release_manager.py" create-repo --spec .github/release-spec.json --visibility public --confirm-create
```

Initialize the local repository only when necessary. Use `main` by default unless the user or project requires another branch. Set the remote, commit intentionally, and push:

```powershell
git init -b main
git add .
git commit -m "Initial release"
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

Do not commit build output. If Git authentication fails, stop and ask the user to authenticate through Git Credential Manager or an appropriately scoped token in their environment. Never put a token into `origin`.

Verify the pushed commit with `git rev-parse HEAD` and the GitHub repository page/API before creating the first release.

## First release

There is no previous release. The update summary should explain:

- the initial product purpose and target users;
- the major capabilities present in this version;
- supported platforms and important limitations;
- all distributed files and their purpose;
- compatibility and upgrade notes, or state explicitly that this is the first public version.

After the repository exists, continue with `release-workflow.md`.
