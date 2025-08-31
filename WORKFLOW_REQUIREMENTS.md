# Claude Code Review Workflow Requirements

## Overview
Enhance the GitHub Actions workflow to provide intelligent, context-aware code reviews powered by Claude Opus 4.1 (Anthropic's most powerful coding model).

## Key Requirements

### 1. Welcome Message on PR Creation
**Trigger:** When a PR is opened (draft or ready)
**Action:** Post ONE introductory comment (only once per PR)
**Message Content:**
- Introduce the Claude code review workflow
- Mention it's powered by Opus 4.1 (Anthropic's best coding model)
- Explain triggering methods:
  - Marking PR as 'ready for review' from draft
  - Tagging @claude in comments
- Should be friendly and informative

**Implementation Notes:**
- Need to track if intro comment was already posted to avoid duplicates
- Could use PR labels or check existing comments

### 2. Context-Aware Response System
The workflow needs to differentiate between different types of interactions:

#### Type A: Full PR Review Request
**Triggers:**
- PR marked as 'ready for review' from draft
- User explicitly asks for a review (e.g., "@claude review this PR")

**Response:**
- Comprehensive code review using the full review prompt
- Check all aspects: code quality, security, performance, testing, documentation
- Post detailed review as PR comment

#### Type B: Specific Questions/Comments
**Triggers:**
- Inline code review comments with @claude mention
- Specific questions in PR comments (e.g., "@claude how should I handle this edge case?")

**Response:**
- Answer the specific question directly
- Don't perform full review unless requested
- Be concise and focused on the query

### 3. Prompt Strategy
The prompt needs to be dynamic based on the trigger context:

**For Full Reviews:**
```
Perform a comprehensive code review focusing on:
- Code quality and best practices
- Security vulnerabilities
- Performance issues
- Test coverage
- Documentation
```

**For Specific Questions:**
```
Context: [inline comment or question]
Please answer the specific question or address the comment directly.
Don't perform a full review unless explicitly requested.
```

## Implementation Plan

### Workflow Updates Needed:

1. **Add PR opened/reopened event:**
   ```yaml
   on:
     pull_request:
       types: [opened, reopened, ready_for_review]
   ```

2. **Separate job for welcome message:**
   - Runs only on `opened` or `reopened`
   - Checks if intro comment exists
   - Posts intro if not present

3. **Enhanced context detection:**
   - Parse comment body to detect review requests vs questions
   - Pass context type to Claude prompt
   - Adjust prompt based on context

4. **Prompt modification:**
   - Add conditional logic in prompt
   - Include original comment/question for context
   - Instruct Claude to be context-aware

## Success Criteria

1. ✅ Each PR gets exactly one introduction comment
2. ✅ Full reviews only trigger when explicitly requested or PR marked ready
3. ✅ Specific questions get direct, focused answers
4. ✅ No unnecessary full reviews on simple questions
5. ✅ Workflow is intuitive and doesn't spam PR with comments

## Technical Considerations

- Use GitHub API to check for existing intro comments
- Consider using PR labels to track workflow state
- Ensure idempotency - repeated triggers shouldn't duplicate actions
- Handle edge cases (deleted comments, edited triggers, etc.)