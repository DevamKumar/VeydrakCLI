# Contributing to Veydrak

We welcome contributions to Veydrak! 

## Development Environment Setup

1. Clone the repository
2. Set up a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install development dependencies: `pip install -e ".[dev]"`

## Repository Structure

- `src/veydrak/`: Core implementation
- `examples/`: Standalone scripts demonstrating agent behaviors
- `tests/`: Pytest test suite
- `docs/`: Architecture documentation

## Running Tests

We use `pytest` for all testing.
```bash
pytest tests/
```

## Adding Features

- **Do not break existing LangGraph workflows.** Veydrak's orchestrator is highly tuned. If you are adding a node, ensure it is thoroughly tested.
- **Update schemas carefully.** Structured outputs rely on `src/veydrak/schemas/schemas.py`.
- **Add tests.** Any new functionality should be accompanied by integration tests in `tests/`.

## Creating Pull Requests

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes with clear messages.
4. Push to your fork and submit a PR against `main`.
5. Ensure GitHub Actions CI passes (tests and linting).
