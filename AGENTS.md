# AGENTS.md

## Scope

These instructions apply to the entire repository.

## Development environment: uv

- Use [uv](https://docs.astral.sh/uv/) as the only project and dependency manager.
- Keep project metadata and all runtime, test, and documentation dependencies in `pyproject.toml`.
- Commit `uv.lock` and keep it synchronized with `pyproject.toml`.
- Do not add or maintain `requirements.txt` files, and do not use `pip install` in project workflows.
- Add runtime dependencies with `uv add <package>`.
- Add development-only dependencies with `uv add --group dev <package>`.
- Run Python tools through `uv run`; do not rely on globally installed tools.
- Bootstrap or update the environment with:

  ```bash
  uv sync --all-groups
  ```

## Test-driven development

All behavior changes and bug fixes must follow test-driven development:

1. Write or update a focused test that describes the desired behavior.
2. Run the test and confirm it fails for the expected reason.
3. Implement the smallest change that makes the test pass.
4. Refactor while keeping the test suite green.
5. Run the complete test suite before finishing.

Use `pytest` and run tests through uv:

```bash
uv run pytest
```

For a focused iteration, run the smallest relevant test first:

```bash
uv run pytest tests/path/to/test_file.py -q
```

Tests must not depend on real laboratory servers, live SSH connections, or external download services. Mock network, SSH, filesystem, subprocess, and release-download boundaries where appropriate.

A change is not complete unless its behavior is covered by tests. If a change cannot reasonably be tested, document the reason explicitly.

## Documentation: Sphinx + Markdown

- Maintain the project documentation under `docs/` using Sphinx.
- Author documentation in Markdown and parse it with MyST Parser.
- Keep `docs/conf.py` as the Sphinx configuration entry point.
- Organize the documentation through a Markdown root document and MyST `toctree` directives.
- Update the documentation whenever commands, configuration, architecture, deployment, or user-visible behavior changes.
- Include copy-pasteable commands and configuration examples where practical.
- Treat documentation warnings as errors.

Build the documentation through uv:

```bash
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Do not commit generated documentation output from `docs/_build/`.

## Required verification

Before considering a task complete, run:

```bash
uv sync --all-groups
uv run pytest
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Report any command that could not be run and explain why.
