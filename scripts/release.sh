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
  --github-release          Create a GitHub release with gh and upload the ZIP.
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
  if ! command -v gh >/dev/null 2>&1; then
    echo "GitHub CLI is required for --github-release but was not found in PATH." >&2
    exit 1
  fi
  REMOTE_URL="$(git config --get "remote.$REMOTE.url")"
  GH_REPO="$REMOTE_URL"
  GH_REPO="${GH_REPO#git@github.com:}"
  GH_REPO="${GH_REPO#https://github.com/}"
  GH_REPO="${GH_REPO%.git}"
  if [[ ! "$GH_REPO" =~ ^[^/]+/[^/]+$ ]]; then
    echo "Could not infer GitHub owner/repo from remote '$REMOTE': $REMOTE_URL" >&2
    exit 1
  fi
  gh release create "$TAG" "$ZIP_PATH" \
    --repo "$GH_REPO" \
    --title "$TAG" \
    --notes-file "$NOTES_PATH"
fi

echo "Release prepared: $TAG"
echo "ZIP: $ZIP_PATH"
echo "Notes: $NOTES_PATH"
