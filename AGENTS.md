# Codex Project Instructions

## Release Workflow

When the user asks to make a release, use the local release tooling instead of
recreating the steps manually.

Default release command:

```bash
scripts/release.sh <version> --remote github --push --github-release
```

Use a plain semantic version without the `v` prefix, for example `0.1.4`.
The script creates the `v<version>` tag.

If GitHub authentication is not available, run the same command without
`--github-release`, or without `--push`, then report exactly what remains to be
done. The supported GitHub release setups are:

- `GITHUB_TOKEN` exported in the shell. The token must have permission to create
  releases and upload release assets for this repository.
- `gh auth login`, if GitHub CLI is installed.
- an SSH GitHub remote, so `git push github main v<version>` works without an
  interactive HTTPS username prompt.

Release output conventions:

- Integration domain: `technitium_dns`
- Manifest: `custom_components/technitium_dns/manifest.json`
- ZIP asset: `dist/technitium_dns-v<version>.zip`
- Release notes: `dist/release-notes-v<version>.md`
- Tag format: `v<version>`
- Commit message: `Release v<version>`

Do not include unrelated local changes in the release commit. In particular,
leave a pre-existing `.gitignore` modification alone unless the user explicitly
asks to include it.

Before publishing, the release script verifies Python syntax with:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/ha_technitium_pycache python3 -m compileall custom_components/technitium_dns
```

The GitHub release body should come from `dist/release-notes-v<version>.md`,
generated from `.github/release-template.md`.
