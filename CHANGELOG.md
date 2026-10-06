# Changelog

Release notes for PDF Machinator, in plain language. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

The **`[Unreleased]`** section collects entries as they land on `main`. When cutting a release,
rename it to the new version + date, start a fresh empty `[Unreleased]` above it, then push the
`vX.Y.Z` tag. `.github/workflows/release.yml` copies the section matching the tag straight into the
GitHub release notes, so write every entry the way it should read there.

## [Unreleased]

## [1.0.0] - 2026-10-06

First release.

### Added

- **Insert text between the letters** (e.g. a missing comma), in the size and baseline of the surrounding
  line, with a custom text colour and an optional background with adjustable opacity.
- **Notes** (sticky-note icon): click to read, edit or delete; they show up in other PDF viewers too.
- **Highlighter** and **circle / ellipse** tools (Shift = perfect circle), each with an optional comment.
- **Layout-safe saving:** annotations are appended to the file (incremental save), the original page
  content is never rewritten. Save and Save As, undo.
- Colour picker with favourite colours, eyedropper and opacity.
- Icon toolbar, keyboard shortcuts, zoom, fit width, page navigation.
- English, German and Hungarian UI: follows the OS language, switchable from the *Language* menu.
- Builds for Windows, macOS (Apple Silicon and Intel) and Linux.
