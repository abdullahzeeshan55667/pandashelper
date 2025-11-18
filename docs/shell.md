# Interactive Teaching Shell

The teaching shell is a friendlier Python REPL that keeps lesson progress close
by and preloads common data analysis helpers. Launch it with:

```bash
python -m session.teaching_shell --progress-file progress.json
```

## Why use this shell?
- Immediate access to pandas (`pd`) and helper functions like
  `load_dataset`, `clean_column_names`, `summarize_numeric`, and
  `fill_missing`.
- Inline lesson helpers: list lessons, mark them complete, and attach notes
  without leaving the REPL.
- Readline history (stored at `~/.pandashelper_history` by default) so you can
  recall commands across sessions.
- Optional CSV preload so learners can start manipulating data right away:
  `python -m session.teaching_shell --preload-csv people.csv --preload-var people`.

## Commands
- `:help` — show available commands.
- `:lessons` — list lesson keys and summaries.
- `:summary` — view completed and pending lessons plus notes.
- `:complete <key> [note]` — mark a lesson complete with an optional note.
- `:note <key> <text>` — add or replace a note for a lesson.
- `:loadcsv <path> [var]` — load a CSV into a variable (default `df`).
- `:reset` — clear progress and notes.
- `:save` — save progress immediately.
- `:quit` or `:exit` — save and leave the shell.

All other input is treated as Python code. Multi-line blocks are supported
just like the standard REPL.
