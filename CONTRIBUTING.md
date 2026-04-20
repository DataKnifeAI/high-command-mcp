# Contributing to High-Command

Thank you for your interest in contributing to High-Command! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and professional in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/high-command.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up development environment: `make dev`

## Development Workflow

### Before Making Changes

- Check existing issues and pull requests
- Discuss major changes in an issue first
- Review `.github/copilot-instructions.md` for development patterns

### Making Changes

1. **Write tests first** (TDD approach)
2. Implement the feature
3. Run linters and formatters:
   ```bash
   make format
   make lint
   ```
4. Run tests:
   ```bash
   make test
   ```

### Code Style

- Follow PEP 8
- Use type hints for all functions and methods
- Maximum line length: 100 characters
- Docstrings for all public functions/classes
- Use Pydantic v2 for data validation
- Use async/await for all I/O operations

### Rate Limiting Best Practices

When working with the API client:

1. **The MCP client does NOT implement automatic retries** - Design your features accordingly
2. **Implement exponential backoff** at the application level when needed (see `docs/API.md#rate-limiting`)
3. **Cache responses** when appropriate to minimize API calls
4. **Add tests** for rate limit handling in your features
5. **Log rate limit events** using structured logging: `logger.warning("Rate limit exceeded", endpoint=...)`
6. **Document retry behavior** if your feature implements custom retry logic

### Project Structure

- **`highcommand/`** - Main package code
- **`tests/`** - Unit tests
- **`docs/`** - Project documentation
- **`.github/`** - GitHub Actions workflows and development instructions

### Adding New Features

Follow this pattern (see `.github/copilot-instructions.md` for details):

1. Add method to `highcommand/api_client.py` if it's an API feature
2. Add Pydantic model in `highcommand/models.py` if needed
3. Add tool method in `highcommand/tools.py`
4. Register tool in `highcommand/server.py` (2 places)
5. Write tests in `tests/test_*.py`
6. Update docs in `docs/API.md`

### Commit Messages

- Use clear, descriptive messages
- Start with a verb: "Add", "Fix", "Update", "Refactor"
- Keep commits focused and atomic
- Reference issues: "Fixes #123"

Example:
```
Add support for biomes endpoint

- Implement get_biomes method in APIClient
- Add get_biomes_tool wrapper
- Register biomes tool in MCP server
- Add tests for biomes functionality
- Update API documentation

Fixes #45
```

### Testing

- Write unit tests for new code
- Use `pytest` and `pytest-asyncio`
- Aim for >80% coverage
- Run with: `make test`

### Pull Request Process

1. Update documentation as needed
2. Add tests for new functionality
3. Ensure all tests pass: `make test`
4. Run linters: `make lint`
5. Format code: `make format`
6. Create PR with clear description
7. Link related issues
8. Request review from maintainers

### Documentation

- Update `docs/` files for user-facing changes
- Update `.github/copilot-instructions.md` for development patterns
- Add docstrings to all public functions
- Keep README.md up to date

## Development Resources

- **`.github/copilot-instructions.md`** - Comprehensive development guide
- **`docs/SETUP.md`** - Installation and environment setup
- **`docs/API.md`** - API endpoint documentation
- **`docs/CONTRIBUTING.md`** - Contribution guidelines (in docs folder)
- **`Makefile`** - Common development tasks

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Tests pass: `make test`
- [ ] Code formatted: `make format`
- [ ] No lint errors: `make lint`
- [ ] Docstrings added for public functions
- [ ] Type hints included
- [ ] No breaking changes documented
- [ ] PR description is clear and complete
- [ ] Related issues are linked

## Questions?

- Check the documentation in `docs/`
- Review `.github/copilot-instructions.md` for patterns
- Look at existing code for examples
- Open an issue to discuss ideas

## License

By contributing to High-Command, you agree that your contributions will be licensed under the Apache License, Version 2.0.

---

**Thank you for contributing to High-Command! 🎉**
