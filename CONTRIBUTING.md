# Contributing to GitHub Diff Email Notifier

Thank you for your interest in contributing! 🎉

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit:** `git commit -m 'Add amazing feature'`
6. **Push:** `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/github-diff-emailer.git
cd github-diff-emailer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with test credentials

# Run tests
python test_emailer.py

# Start development server
python webhook_server.py
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Update documentation for new features

## Testing

- Test with real GitHub webhooks
- Test with different email providers
- Test error scenarios
- Verify email formatting

## Reporting Issues

When reporting issues, please include:
- Your environment (OS, Docker version)
- Email provider (AWS SES, Gmail, etc.)
- Error messages and logs
- Steps to reproduce

## Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Describe the use case
- Explain expected behavior

Thank you! 🙏
