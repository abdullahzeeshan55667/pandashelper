# Python Teaching Companion

A beginner-friendly repository that collects concise Python learning docs, data analysis modules, and lightweight tooling for running teaching sessions that save learner progress.

## What you get
- **Curriculum outlines** covering Python basics and introductory data analysis.
- **LLM-friendly prompts** to launch a teaching session and record progress for a learner.
- **Runnable helpers** so a tutor (human or LLM) can mark lessons complete and persist notes.
- **Interactive teaching shell** that preloads pandas utilities and lesson commands for quick practice.

## Quickstart
1. Launch the interactive teaching shell with pandas helpers preloaded:
   ```bash
   python -m session.teaching_shell --progress-file progress.json
   ```
2. Create a progress file (defaults to `progress.json`):
   ```bash
   python -m session.teaching_session --progress-file progress.json --list-lessons
   ```
3. Mark a lesson complete with optional notes:
   ```bash
   python -m session.teaching_session --progress-file progress.json --complete variables --notes "Understood variable naming and types"
   ```
4. View a summary of completed and pending lessons:
   ```bash
   python -m session.teaching_session --progress-file progress.json --summary
   ```

## Project layout
- `curriculum/` — lesson overviews for Python fundamentals and data analysis.
- `docs/` — guidance on running sessions and using the material.
- `modules/` — reusable Python snippets for data analysis practice.
- `session/` — the teaching session runner, interactive shell, and LLM prompt.

## Suggested next steps
- Expand the curriculum with exercises and quizzes.
- Add more data analysis case studies using the helpers in `modules/data_analysis.py`.
- Hook the session runner into a chat UI so learners can progress asynchronously.
- Run the interactive shell for a friendly, pandas-ready REPL: `python -m session.teaching_shell`.
