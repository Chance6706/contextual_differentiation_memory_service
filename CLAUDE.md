# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

1. Plan mode by default. Enter plan mode for any task with 3+ steps or architectural decisions. If something goes sideways, stop and re-plan immediately. Write detailed specs upfront to reduce ambiguity.

2. Use subagents liberally. Offload research, exploration, and parallel analysis to subagents. Keep your main context window clean. For complex problems, throw more compute at it. One task per subagent for focused execution.

3. Verify before marking done. Never mark a task complete without testing that it works. Diff behavior between main and your changes.

4. Let Claude fix bugs autonomously. When given a bug report, just fix it. Point at logs, errors, failing tests and resolve them. Go fix failing CI tests without being told how.

5. Do not assume context. If critical context is missing, ask first.

6. Separate fact from inference. Never present guesses as answers.

7. Avoid overconfidence. Don't state uncertain things as definitive.

8. Acknowledge disagreement. If sources conflict, say so and summarize both sides.

9. Do not restrict yourself to a single point of view. If it cannot be stress-tested then it cannot be properly implemented.