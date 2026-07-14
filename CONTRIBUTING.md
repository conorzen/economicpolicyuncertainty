# Contributing

## Setup

```bash
git clone https://github.com/conorzen/economicpolicyuncertainty.git
cd economicpolicyuncertainty
uv sync
```

## Running the tests

`test.py` is a live integration test — it hits policyuncertainty.com and
exercises the public API end to end. There's no mocked test suite, since the
main risk in this project is the upstream site changing a URL or file layout,
which only a real fetch will catch.

```bash
uv run python test.py
```

If you're only changing/adding a registry entry, `check_sources.py` is
faster — it just fetches and parses every series without going through the
DB/cache layer:

```bash
uv run python check_sources.py
```

Both scripts create a local `economicpolicyuncertainty.db` cache file; it's
gitignored and safe to delete between runs.

## Adding or fixing a series

Series live as plain dicts in `economicpolicyuncertainty/registry.py`. See
the module docstring there for what each field (`shape`, `date_mode`,
`confidence`, etc.) means. After adding or editing an entry, run
`check_sources.py` and confirm it reports `OK` with a plausible row count
before opening a PR.

## Pull requests

- All changes to `main` go through a PR — direct pushes are blocked.
- Keep PRs focused; unrelated cleanup belongs in its own PR.
- Bump the `version` in `pyproject.toml` and add a `CHANGELOG.md` entry for
  any user-facing fix or feature. Releases are cut by tagging a GitHub
  Release (`vX.Y.Z`), which triggers `.github/workflows/publish.yml` to
  build and publish to PyPI automatically — no manual `uv publish` needed.
- Match the existing code style: no comments unless they explain a
  non-obvious *why*: no docstrings restating what a function already makes
  obvious from its name and signature.
