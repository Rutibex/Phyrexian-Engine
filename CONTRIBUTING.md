# Contributing

Thanks for your interest!

## Dev environment
1. Create a virtualenv and install requirements:
   ```
   python -m venv .venv
   . .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Run the UI:
   ```
   python -m phyrexian_engine
   ```

## Code style
- Keep functions small and focused.
- Prefer dataclasses for model types.
- Templates live in `packages/*.json`. Weights and MV ranges keep things reasonable.

## Tests
If you add nontrivial logic, please include a minimal test in `tests/` (create if absent).

## License
By contributing, you agree your code will be licensed under the repository’s LICENSE.
