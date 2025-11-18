# Running a Teaching Session

Use the teaching session runner to coordinate lessons, persist progress, and keep tutoring aligned.

## Commands
- Try the interactive shell for a lesson-aware REPL:
  ```bash
  python -m session.teaching_shell --progress-file progress.json
  ```

- List available lessons:
  ```bash
  python -m session.teaching_session --list-lessons
  ```
- Mark a lesson complete with optional notes:
  ```bash
  python -m session.teaching_session --complete functions --notes "Understands parameters and return values"
  ```
- Show progress summary:
  ```bash
  python -m session.teaching_session --summary
  ```

## Tips for tutors
- Keep one `progress.json` per learner so they can resume later.
- Use the `resources` links in each lesson to point learners to concise docs.
- Encourage hands-on practice with the helper functions in `modules/data_analysis.py`.
