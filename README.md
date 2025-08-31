# Workflow Test Repository

This repository is used for testing GitHub Actions workflows.

## Purpose

This repository serves as a testing ground for developing and refining GitHub Actions workflows, particularly focusing on automated code review capabilities.

## Test File

This is a simple file for testing pull request reviews.

## Key Features

- Automated PR welcome messages
- Context-aware code review responses
- Support for multiple interaction types

## Claude Code Review Workflow

This repository includes an automated code review workflow powered by Claude that provides comprehensive analysis of pull requests.

### Features

- **Automated Code Review**: Claude automatically reviews pull requests when triggered
- **Multi-Event Support**: Responds to:
  - Pull request comments (issue_comment on PRs)
  - Pull request review comments (pull_request_review_comment)
  - Pull requests marked as ready for review (pull_request ready_for_review)
- **Security-First**: Only users with write, maintain, or admin permissions can trigger reviews
- **Comprehensive Analysis**: Reviews code quality, security, performance, testing, and documentation

### How to Trigger a Review

1. **On PR Comments**: Comment `@claude review` on a pull request
2. **On Review Comments**: Reply to any code review comment mentioning Claude
3. **Automatic on Ready**: Reviews automatically trigger when a PR is marked as ready for review

### Required Permissions

- Users must have `write`, `maintain`, or `admin` permissions on the repository
- The workflow validates permissions before executing any review actions

### Configuration

The workflow requires the following secrets:
- `CLAUDE_CODE_OAUTH_TOKEN`: Authentication token for Claude Code action
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
