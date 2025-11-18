"""Interactive teaching shell with lesson helpers and progress tracking.

This shell wraps Python's :mod:`code` interactive console so beginners (or an
LLM tutor) can run code, load CSVs, and mark lessons complete from one place.

Commands start with a leading ``:``. Everything else is treated as Python code
and executed in a preloaded environment that already includes pandas and the
data-analysis helpers from :mod:`modules.data_analysis`.
"""

from __future__ import annotations

import argparse
import code
import readline
from pathlib import Path
from typing import Dict, List

import pandas as pd

from modules.data_analysis import (
    clean_column_names,
    fill_missing,
    load_dataset,
    profile_dataframe,
    sample_sales_data,
    summarize_numeric,
)
from session.teaching_session import (
    DEFAULT_LESSONS,
    Lesson,
    complete_lesson,
    list_lessons,
    load_progress,
    save_progress,
    summarize_progress,
)


HELP_TEXT = """Commands:
:help                 Show this help message
:lessons              List available lessons
:summary              Show progress summary
:complete KEY [note]  Mark a lesson complete with an optional note
:note KEY TEXT        Add or replace a note for a lesson
:loadcsv PATH [var]   Load a CSV into a variable (default: df)
:reset                Clear all progress
:save                 Save progress to disk immediately
:exit / :quit         Save progress and exit

All other input is executed as Python code. The shell is preloaded with:
- pandas as pd
- load_dataset, clean_column_names, summarize_numeric, fill_missing
- profile_dataframe, sample_sales_data
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--progress-file",
        type=Path,
        default=Path("progress.json"),
        help="Path to the progress JSON file",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=Path.home() / ".pandashelper_history",
        help="Path to store shell history (readline)",
    )
    parser.add_argument(
        "--preload-csv",
        type=Path,
        help="Optionally load a CSV into the shell as a DataFrame",
    )
    parser.add_argument(
        "--preload-var",
        default="df",
        help="Variable name for the --preload-csv DataFrame (default: df)",
    )
    return parser.parse_args()


class TeachingShell:
    """Interactive shell that mixes lesson management with Python execution."""

    def __init__(self, *, progress_file: Path, history_file: Path, lessons: List[Lesson]):
        self.progress_file = progress_file
        self.history_file = history_file
        self.lessons = lessons
        self.progress: Dict = load_progress(progress_file)

        self.env = {
            "pd": pd,
            "Path": Path,
            "load_dataset": load_dataset,
            "clean_column_names": clean_column_names,
            "summarize_numeric": summarize_numeric,
            "fill_missing": fill_missing,
            "profile_dataframe": profile_dataframe,
            "sample_sales_data": sample_sales_data,
        }
        self.console = code.InteractiveConsole(self.env)

        self._load_history()

    # history helpers
    def _load_history(self) -> None:
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
        readline.set_history_length(500)

    def _save_history(self) -> None:
        try:
            readline.write_history_file(self.history_file)
        except FileNotFoundError:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(self.history_file)

    # progress helpers
    def _save_progress(self) -> None:
        save_progress(self.progress_file, self.progress)

    def _handle_command(self, line: str) -> bool:
        """Return True to continue, False to exit."""

        if not line:
            return True

        if not line.startswith(":"):
            more = self.console.push(line)
            self._maybe_prompt_continuation(more)
            return True

        parts = line[1:].strip().split()
        if not parts:
            return True

        cmd, *args = parts

        if cmd in {"exit", "quit"}:
            return False
        if cmd == "help":
            print(HELP_TEXT)
            return True
        if cmd == "lessons":
            print(list_lessons(self.lessons))
            return True
        if cmd == "summary":
            print(summarize_progress(self.lessons, self.progress))
            return True
        if cmd == "complete":
            if not args:
                print("Usage: :complete <lesson_key> [note]")
                return True
            key = args[0]
            note = " ".join(args[1:]) if len(args) > 1 else None
            self.progress = complete_lesson(self.progress, key, note)
            self._save_progress()
            print(f"Marked '{key}' complete. Progress saved.")
            return True
        if cmd == "note":
            if len(args) < 2:
                print("Usage: :note <lesson_key> <text>")
                return True
            key = args[0]
            text = " ".join(args[1:])
            self.progress.setdefault("notes", {})[key] = text
            self._save_progress()
            print(f"Stored note for '{key}'.")
            return True
        if cmd == "loadcsv":
            if not args:
                print("Usage: :loadcsv <path> [var]")
                return True
            path = Path(args[0])
            var_name = args[1] if len(args) > 1 else "df"
            df = load_dataset(path)
            self.console.locals[var_name] = df
            print(f"Loaded {path} into variable '{var_name}' (rows={len(df)}).")
            return True
        if cmd == "reset":
            self.progress = {"completed": [], "notes": {}}
            self._save_progress()
            print("Progress cleared.")
            return True
        if cmd == "save":
            self._save_progress()
            print(f"Progress saved to {self.progress_file}.")
            return True

        print(f"Unknown command: {cmd}. Type :help for options.")
        return True

    def _maybe_prompt_continuation(self, need_more: bool) -> None:
        if need_more:
            # indicate that more input is expected (e.g., after a colon or open block)
            print("...", end="")
            print()

    def run(self) -> None:
        print("Python Teaching Shell (type :help for commands)")
        print(list_lessons(self.lessons))
        print(summarize_progress(self.lessons, self.progress))

        try:
            while True:
                try:
                    line = input("learn> ")
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\n(Interrupted — type :quit to exit)")
                    continue

                if not self._handle_command(line.rstrip("\n")):
                    break
        finally:
            self._save_progress()
            self._save_history()
            print(f"Progress saved to {self.progress_file}.")


def main() -> None:
    args = parse_args()
    shell = TeachingShell(
        progress_file=args.progress_file,
        history_file=args.history_file,
        lessons=DEFAULT_LESSONS,
    )

    if args.preload_csv:
        df = load_dataset(args.preload_csv)
        shell.console.locals[args.preload_var] = df
        print(f"Preloaded {args.preload_csv} into variable '{args.preload_var}'.")

    shell.run()


if __name__ == "__main__":
    main()
