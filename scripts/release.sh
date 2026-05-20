#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTEGRATION_NAME="technitium_dns"
MANIFEST="$ROOT_DIR/custom_components/$INTEGRATION_NAME/manifest.json"
README="$ROOT_DIR/README.md"
TEMPLATE="$ROOT_DIR/.github/release-template.md"
DIST_DIR="$ROOT_DIR/dist"
REMOTE="github"
PUSH=false
GITHUB_RELEASE=false
CHANGE_SUMMARY=""

usage() {
  cat <<'USAGE'
Usage:
  scripts/release.sh <version> [options]

Arguments:
  <version>                 Semantic version without the v prefix, e.g. 0.1.4.

Options:
  --remote <name>           Git remote to push to. Default: github.
  --push                    Push main and the tag to the selected remote.
  --github-release          Create a GitHub release and upload the ZIP.
                            Uses gh if available, otherwise GITHUB_TOKEN + curl.
  --change-summary <text>   One-line release summary for the release notes.
  -h, --help                Show this help.

Examples:
  scripts/release.sh 0.1.4
  scripts/release.sh 0.1.4 --remote github --push --github-release
USAGE
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

VERSION="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --push)
      PUSH=true
      shift
      ;;
    --github-release)
      GITHUB_RELEASE=true
      PUSH=true
      shift
      ;;
    --change-summary)
      CHANGE_SUMMARY="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must use semantic version format without a v prefix, e.g. 0.1.4." >&2
  exit 2
fi

if [[ -z "$REMOTE" ]]; then
  echo "Remote cannot be empty." >&2
  exit 2
fi

infer_github_repo() {
  local remote_url gh_repo
  remote_url="$(git config --get "remote.$REMOTE.url")"
  gh_repo="$remote_url"
  gh_repo="${gh_repo#git@github.com:}"
  gh_repo="${gh_repo#https://github.com/}"
  gh_repo="${gh_repo%.git}"
  if [[ ! "$gh_repo" =~ ^[^/]+/[^/]+$ ]]; then
    echo "Could not infer GitHub owner/repo from remote '$REMOTE': $remote_url" >&2
    return 1
  fi
  printf '%s\n' "$gh_repo"
}

create_github_release_with_token() {
  local gh_repo release_json upload_url release_id asset_name
  gh_repo="$1"
  asset_name="$(basename "$ZIP_PATH")"

  release_json="$(
    python3 - "$TAG" "$NOTES_PATH" <<'PY'
import json
import sys
from pathlib import Path

tag = sys.argv[1]
notes = Path(sys.argv[2]).read_text()
print(json.dumps({
    "tag_name": tag,
    "name": tag,
    "body": notes,
    "draft": False,
    "prerelease": False,
}))
PY
  )"

  release_id="$(
    curl -fsS \
      -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/$gh_repo/releases" \
      -d "$release_json" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])'
  )"

  upload_url="https://uploads.github.com/repos/$gh_repo/releases/$release_id/assets?name=$asset_name"
  curl -fsS \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/zip" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$upload_url" \
    --data-binary "@$ZIP_PATH" \
    >/dev/null
}

TAG="v$VERSION"
ZIP_PATH="$DIST_DIR/$INTEGRATION_NAME-$TAG.zip"
NOTES_PATH="$DIST_DIR/release-notes-$TAG.md"

if [[ -z "$CHANGE_SUMMARY" ]]; then
  CHANGE_SUMMARY="Maintenance release for Technitium DNS."
fi

cd "$ROOT_DIR"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Release template not found: $TEMPLATE" >&2
  exit 1
fi

if [[ "$GITHUB_RELEASE" == true ]]; then
  GH_REPO="$(infer_github_repo)"
  if ! command -v gh >/dev/null 2>&1; then
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
      echo "GitHub release creation needs either gh or GITHUB_TOKEN." >&2
      echo "Set GITHUB_TOKEN to a token with repo release permissions, or omit --github-release." >&2
      exit 1
    fi
    if ! command -v curl >/dev/null 2>&1; then
      echo "curl is required when using GITHUB_TOKEN without gh." >&2
      exit 1
    fi
  fi
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag already exists locally: $TAG" >&2
  exit 1
fi

if git diff --name-only --cached | grep -q .; then
  echo "There are already staged changes. Unstage or commit them before releasing." >&2
  exit 1
fi

python3 - "$MANIFEST" "$VERSION" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
version = sys.argv[2]
data = json.loads(path.read_text())
data["version"] = version
path.write_text(json.dumps(data, indent=2) + "\n")
PY

python3 - "$README" "$VERSION" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
version = sys.argv[2]
text = path.read_text()
text = re.sub(r"`v\d+\.\d+\.\d+`", f"`v{version}`", text)
path.write_text(text)
PY

mkdir -p "$DIST_DIR"
rm -f "$ZIP_PATH" "$NOTES_PATH"

PYTHONPYCACHEPREFIX=/private/tmp/ha_technitium_pycache \
  python3 -m compileall "custom_components/$INTEGRATION_NAME"

zip -r "$ZIP_PATH" "custom_components/$INTEGRATION_NAME" \
  -x '*__pycache__*' '*.pyc' '*.pyo' '.DS_Store'

unzip -t "$ZIP_PATH" >/dev/null

python3 - "$TEMPLATE" "$NOTES_PATH" "$VERSION" "$CHANGE_SUMMARY" <<'PY'
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])
version = sys.argv[3]
summary = sys.argv[4]
notes = template.replace("{{VERSION}}", version).replace("{{CHANGE_SUMMARY}}", summary)
out.write_text(notes)
PY

git add "$MANIFEST" "$README"

if [[ -d "custom_components/$INTEGRATION_NAME/brand" ]]; then
  git add "custom_components/$INTEGRATION_NAME/brand"
fi

git commit -m "Release $TAG"
git tag -a "$TAG" -m "$TAG"

if [[ "$PUSH" == true ]]; then
  git push "$REMOTE" main "$TAG"
fi

if [[ "$GITHUB_RELEASE" == true ]]; then
  if command -v gh >/dev/null 2>&1; then
    gh release create "$TAG" "$ZIP_PATH" \
      --repo "$GH_REPO" \
      --title "$TAG" \
      --notes-file "$NOTES_PATH"
  else
    create_github_release_with_token "$GH_REPO"
  fi
fi

echo "Release prepared: $TAG"
echo "ZIP: $ZIP_PATH"
echo "Notes: $NOTES_PATH"
