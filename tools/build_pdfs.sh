#!/usr/bin/env bash
# Copy past papers into app/pdf with the short names the viewer expects.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p app/pdf
for p in 1 2; do
  for f in past-papers/ocr-a-as/paper-$p/*.pdf; do
    b=$(basename "$f")
    case "$b" in Data*) cp "$f" app/pdf/booklet.pdf; continue;; esac
    sess=$(echo "$b" | sed -E 's/ (QP|MS) .*//')
    kind=$(echo "$b" | grep -oE ' (QP|MS) ' | tr -d ' ' | tr A-Z a-z)
    slug=$(echo "$sess" | sed -E 's/June /jun/;s/November /nov/;s/Specimen/specimen/')
    cp "$f" "app/pdf/p$p-$slug-$kind.pdf"
  done
done
