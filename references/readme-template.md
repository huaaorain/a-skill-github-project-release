# README production guide

Use `assets/README.template.md` as the starting structure. The visual reference is [Louis3797/awesome-readme-template](https://github.com/Louis3797/awesome-readme-template), but adapt the result to the actual product and omit irrelevant template sections.

## Required information order

1. Product name, one-sentence purpose, and a real hero image or screenshot.
2. Functional navigation: download, screenshots, installation, documentation, issues.
3. A concise explanation of the problem solved and target user.
4. A feature overview where each major claim maps to real behavior.
5. At least one image in the functional introduction section.
6. Latest-release downloads plus the generated all-version catalog.
7. Installation and first-use instructions.
8. Requirements, data/privacy behavior, and limitations.
9. Build and test instructions for contributors.
10. Contributing, changelog, acknowledgements, and license status.

## Localized READMEs

When the user asks for multiple languages, make each version a complete README rather than a short translation note. Put a compact language switcher immediately below the factual badges and above the navigation links:

```markdown
<p align="center">
  <a href="README.en.md">English</a> ·
  <strong>简体中文</strong> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>
```

Use `README.md` as the primary version unless the repository already has another convention. Keep section order, screenshots, release catalog, and download URLs synchronized. Declare every translated file in `readme.locales`; the helper updates catalogs in all listed files and preflight checks all of them.

## Visual rules

- Use one deliberate visual direction that matches the product; do not stack interchangeable blue badges and generic glowing cards.
- Prefer real screenshots, terminal captures, or diagrams over decorative stock imagery.
- Keep badges limited to useful facts such as version, platform, runtime, or license.
- Put long technical details in `<details>` blocks so the first viewport remains useful.
- Use tables only for genuine comparisons, file inventories, or compatibility matrices.
- GitHub removes `<colgroup>` and `width` attributes during README sanitization. Do not rely on them for table geometry.
- For short CJK labels, keep each label of at most five characters on one line by joining its characters with the narrow no-break space entity `&#8239;`, for example `主&#8239;题&#8239;发&#8239;现`. This lets the table's auto layout widen the first column naturally.
- For labels longer than five characters, insert `<br>` at a meaningful word boundary or allow a full phrase to wrap. Do not leave a line containing only one character.
- Do not add empty "Screenshots coming soon", fake stats, fake testimonials, or placeholder demo links.
- Store images in the repository under `docs/assets/`; do not hotlink temporary local paths.

## Release catalog

Keep these markers exactly once:

```markdown
<!-- release-catalog:start -->
<!-- release-catalog:end -->
```

The helper replaces only this block. It must list every published version, its release date, release-notes link, and download links for every user-facing asset. Drafts stay omitted until published.

## Copy quality

- Describe concrete user outcomes rather than "empowering modern workflows".
- State platform and runtime constraints plainly.
- Do not claim cross-platform support, signing, security, or performance without evidence.
- Keep the README self-contained for users who will never open the source tree.
- Link to deeper documentation rather than placing an entire manual above installation.
