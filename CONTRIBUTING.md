# Contributing to HPSS

Contributions are welcome, especially improvements to the selector, benchmark methodology, tests, documentation, and reproducibility tooling.

## Before opening an issue

Please search existing issues and describe the problem or proposed improvement clearly. For benchmark changes, include the dataset, normalization rules, parameters, and environment needed to reproduce the result.

## Development setup

Use Python 3.11 or newer:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

## Pull requests

1. Keep changes focused and explain the research or software motivation.
2. Add or update tests for behavioral changes.
3. Keep benchmark methodology reproducible and avoid changing datasets or normalization silently.
4. Run the test suite before submitting the pull request.
5. Document externally sourced datasets and pin their provenance when practical.
6. Update the changelog when a change is meaningful to users or reproducibility.

## Research contributions

Changes that alter experimental conclusions should include the exact command or workflow used to generate the new results and should distinguish representation-level collisions from downstream hash collisions.

## Code style

Use clear Python, small testable functions, and comments where an implementation detail is important to correctness or reproducibility.
