# Status Sources and Drift Rules

## Purpose

This document defines which project files describe the current working state and which are intentionally immutable historical snapshots.

## Living status

These files are maintained as living status sources and checked by the automated drift guard:

- `docs/IMPLEMENTATION-STATUS.md` — work actually delivered and still outstanding;
- `docs/ROADMAP.md` — current milestone/gate orientation and prioritization.

The following rules apply to these files:

1. GitHub is the canonical source for the current `main` commit and Issue/PR states.
2. A statically recorded supposedly current `main` SHA is forbidden. It would inevitably become stale after the next merge.
3. A GitHub Issue may be tracked as an open Markdown task (`- [ ] ... #123`) only while GitHub actually reports the Issue as `open`.
4. Gate/milestone merges update the relevant current markers and the next runtime/checkpoint.
5. GitHub Issues and Pull Requests remain the operational source for individual work packages; living-status documents are not a second Issue database.

## Historical snapshots

Dated reviews under `docs/reviews/` are historical evidence. They are not rewritten after creation, even when they contain the `main` SHA, open findings, or Issue states that were current at that time.

The same applies to explicitly dated decision or gate snapshots where the document role identifies them as historical evidence.

The drift guard therefore intentionally does not scan such files.

## Automated guard

`tools/ci/status_drift.py` checks the living-status files.

Locally without network access:

```bash
python3 tools/ci/test_status_drift.py
python3 tools/ci/status_drift.py
```

In Pull Requests, the online check additionally verifies Issues explicitly tracked as open against the GitHub API. It is integrated into the already mandatory `Reuse Review` status check:

```bash
python3 tools/ci/status_drift.py --online
```

The online check uses only `contents: read` and `issues: read`. It writes no GitHub data and requires no external bot or Provider.

## Maintenance responsibility

A PR that changes a gate, milestone, or slice status updates the affected living-status files in the same work context or documents clearly why no change is required there.

Historical reviews remain unaffected. A new gate decision is recorded as a new dated review.
