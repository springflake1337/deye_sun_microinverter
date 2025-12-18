# Contributing to Deye SUN Micro-Inverter Integration

Contributions are welcome! Here's how you can help:

## Reporting Issues

If you find a bug or have a feature request:

1. Check existing issues first
2. Provide:
   - Your inverter model and firmware version
   - Home Assistant version
   - Clear description of the problem
   - Relevant logs (without credentials!)
   - Steps to reproduce

## Testing New Models

If you have a different Deye inverter model:

1. Run: `python test_connection.py --host <IP>`
2. Report any issues or additional data fields found
3. Share the successful test output (without credentials)

## Code Contributions

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with: `python test_integration.py`
5. Submit a pull request

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Comment complex logic

## Testing

Before submitting, ensure:
- `test_integration.py` passes
- `test_connection.py` works with your setup
- No lint errors in Python files
- JSON files are properly formatted

---

**Thank you for contributing!**
