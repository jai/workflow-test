# Testing Guide

## How to Test the Code Review Workflow

### 1. Opening a PR
When you open a new PR, you should see:
- An automatic welcome message from the bot
- Information about Claude Opus 4.1 capabilities

### 2. Triggering Reviews

#### Full Code Review
- Mark PR as "Ready for review" from draft
- Comment "@claude review this PR"
- Comment "@claude please do a full review"

#### Specific Questions
- Comment "@claude what does this function do?"
- Comment "@claude is this secure?"

#### Inline Comments
- Add review comments on specific lines
- Reply with "@claude" to get targeted feedback

### 3. Expected Behaviors

- Welcome message appears only once per PR
- Full reviews only when explicitly requested
- Direct answers to specific questions
- No unnecessary comprehensive reviews for simple queries

## Test Scenarios

- [ ] PR opened - welcome message posted
- [ ] PR reopened - no duplicate welcome
- [ ] "@claude review" - triggers full review
- [ ] "@claude question?" - answers only the question
- [ ] Inline comment with @claude - focused response

## Validation Status

Testing the welcome message functionality with this PR.