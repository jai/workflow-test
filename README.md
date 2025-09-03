# Workflow Test Repository

> A comprehensive testing environment for GitHub Actions workflows with automated code review and implementation capabilities powered by Claude AI.

## 📋 Overview

This repository serves as a testing ground for GitHub Actions workflows, featuring automated code review and implementation workflows powered by Claude AI. It includes sample code (Calculator class) for demonstrating workflow capabilities and comprehensive testing scenarios.

## ✨ Features

### 🤖 Claude AI Integration
- **Automated Code Review**: Intelligent code analysis with security, performance, and best practice recommendations
- **Automated Implementation**: AI-powered code changes and improvements based on review feedback
- **Multi-Event Support**: Responds to various GitHub events for seamless integration
- **Security-First Design**: Permission validation ensures only authorized users can trigger actions

### 📦 Sample Code Components
- **Calculator Class**: A demonstration class with arithmetic operations
- **Comprehensive Test Suite**: Full test coverage with edge cases and validation
- **Example Usage**: Practical examples for testing workflow behaviors

## 🚀 Getting Started

### Prerequisites
- Node.js (for running the Calculator example)
- GitHub repository with write/maintain/admin permissions
- Required GitHub secrets configured (see Configuration section)

### Installation
```bash
# Clone the repository
git clone https://github.com/jai/workflow-test.git
cd workflow-test

# Install dependencies (if any)
npm install

# Run tests
npm test
```

## 💬 Workflow Usage

### Claude Code Review Workflow

#### Triggering a Code Review
```
@claude review this PR
```

The review workflow will:
1. Analyze code quality, security, and performance
2. Check test coverage and documentation
3. Suggest improvements and best practices
4. Provide comprehensive feedback as PR comments

#### Requesting Implementation
```
@claude-implement add error handling to the main function
```

The implementation workflow will:
1. Parse the requested changes
2. Modify the relevant files
3. Create appropriate commits with GPG signing
4. Push changes to the PR branch

### Supported GitHub Events
- `issue_comment`: Triggered by comments on pull requests
- `pull_request_review_comment`: Triggered by review comments on code
- `pull_request`: Triggered when PR is marked as ready for review

## 🔧 Configuration

### Required GitHub Secrets
| Secret Name | Description | Required |
|------------|-------------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Authentication token for Claude Code action | ✅ |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions | ✅ |
| `GPG_PRIVATE_KEY` | GPG private key for commit signing | Optional |
| `GPG_PASSPHRASE` | Passphrase for GPG key | Optional |

### Workflow Permissions
Users must have one of the following permissions to trigger workflows:
- `write` - Can trigger reviews and implementations
- `maintain` - Full workflow access
- `admin` - Complete control over workflows

## 📁 Project Structure
```
workflow-test/
├── .github/
│   └── workflows/        # GitHub Actions workflow definitions
├── calculator.js          # Sample Calculator class
├── calculator.test.js     # Comprehensive test suite
├── example.py            # Python example file
├── README.md             # This file
└── WORKFLOW_REQUIREMENTS.md  # Detailed workflow specifications
```

## 🧪 Testing Guidelines

### Running Tests Locally
```bash
# Run all tests
npm test

# Run specific test file
npm test calculator.test.js

# Run with coverage
npm test -- --coverage
```

### Test Data Requirements
- Numeric inputs for Calculator operations
- Edge cases: zero, negative numbers, decimals
- Invalid inputs: strings, null, undefined, Infinity, NaN

### Expected Outcomes
- All arithmetic operations return correct results
- Error handling for invalid inputs
- History tracking for all operations
- Proper validation of finite numbers

## 🐛 Troubleshooting

### Common Issues

#### Workflow Not Triggering
- **Issue**: Comment with @claude doesn't trigger workflow
- **Solution**: Ensure you have write/maintain/admin permissions on the repository

#### GPG Signing Failures
- **Issue**: Commits are not GPG signed
- **Solution**: Verify GPG secrets are correctly configured and the email matches your GitHub account

#### Permission Denied Errors
- **Issue**: Workflow fails with permission errors
- **Solution**: Check that GITHUB_TOKEN has appropriate permissions in workflow file

### FAQ

**Q: Can I use this in my own repository?**
A: Yes! Fork this repository and configure the required secrets in your GitHub settings.

**Q: How do I customize the Claude responses?**
A: Modify the workflow files in `.github/workflows/` to adjust prompts and behaviors.

**Q: Is there a rate limit for Claude reviews?**
A: Rate limits depend on your Claude Code plan. Check your usage in the GitHub Actions tab.

## 📚 Documentation

- [WORKFLOW_REQUIREMENTS.md](./WORKFLOW_REQUIREMENTS.md) - Detailed workflow specifications
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is used for testing purposes. See your organization's licensing guidelines for production use.

## 👥 Support

For issues or questions:
- Open an issue in this repository
- Contact the repository maintainers
- Check the troubleshooting section above

---

*Built with ❤️ for testing GitHub Actions workflows with Claude AI*
