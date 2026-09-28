# Branches, versions and release notes

## The model

| Ref | What it holds |
|-----|---------------|
| `main` | The **latest published version**, plus repository-level docs (README, LICENSE, this file). |
| `X.Y.Z` (for example `4.2.1`) | One branch per version. The state of the code at that release, plus that version's notes in `docs/release/`. |
| `vX.Y.Z` tags | Immutable pointers to each release. Prefer a tag when you need to pin. |
| `roadmap` | Documentation only: the plan for the versions that do not exist yet. Never merged. |
| `chore/…`, `fix/…` | Short-lived working branches, merged into `main` by fast-forward and deleted. |

Older versions stay available as branches, so `git switch 4.1.0` (or a tag) shows exactly what
that release looked like, including its own release notes.

## `docs/release/` — one folder, replaced on every version

Each version branch carries its own notes under the **same path**, `docs/release/`:

| File | Purpose |
|------|---------|
| `PLAN.md` | Scope: which problems the version fixes, where each came from, the probable solution. |
| `TODO.md` | Checklist of the work, updated while the version is built. |
| `NOTES.md` | Verification results and anything left for later (optional). |

Because the path is fixed and the first commit of every new version branch removes the
previous version's folder, **a branch shows only its own version's files**, and `main` shows
the latest version's. Nothing accumulates. Versions published before this model was adopted
have no `docs/release/`.

## Opening the next version

```bash
git switch main
git switch -c 4.2.2
git rm -r docs/release            # drop the previous version's notes
mkdir -p docs/release             # add PLAN.md and TODO.md for 4.2.2
git add docs/release && git commit -m "docs(release): plan for 4.2.2"
# ...work, one commit per topic, updating docs/release/TODO.md and CHANGELOG.md...
```

To publish: run the checks, tag the tip (`git tag v4.2.2`), then fast-forward `main` to the
branch and push the branch, the tag and `main`.

Only the **next** version gets a branch; later ones are described on `roadmap` until their turn,
so no future branch goes stale.
