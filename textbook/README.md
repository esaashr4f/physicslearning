# Textbook

Put the AS Physics textbook here (private use only; this repo is private).

## Size limits

GitHub limits apply even to private repositories:

| How you upload | Largest single file |
|---|---|
| GitHub website (drag and drop / "Add file → Upload files") | 25 MB |
| `git push` from your computer | 100 MB |
| Git LFS (Large File Storage) | 2 GB (free quota: 1 GB storage, 1 GB transfer per month) |

A 200 MB PDF needs one of the options below.

## Options, easiest first

1. **Export the text only** (best for analysis, usually 2–5 MB):
   Adobe Acrobat → File → Export to → Text, or Preview (Mac) → File → Export as Text.
   Save it here as `textbook.txt`.
2. **Split into chapters** under 25 MB each (any PDF splitter, e.g. Preview, Acrobat,
   or ilovepdf "Split PDF"), then upload through the GitHub website. Name them in order:
   `01-chapter-name.pdf`, `02-chapter-name.pdf`, …
3. **Compress** the PDF (ilovepdf "Compress PDF", or Preview → Export → Quartz filter
   "Reduce File Size"). Image-heavy books often shrink by 80–90%.
4. **Git LFS** for the whole file from your computer:
   ```
   git lfs install
   git lfs track "textbook/*.pdf"
   git add .gitattributes textbook/
   git commit -m "Add textbook"
   git push
   ```

## Which branch

Upload to the branch `claude/elegant-davinci-o8eqht` (the one this project uses), or to
`main` and say so, and it will be picked up from there.
