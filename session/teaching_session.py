"""Lightweight teaching session runner that saves learner progress to disk.

The script is intentionally simple so LLMs can drive it by calling command-line
flags. Lessons are defined here but can be extended.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class Lesson:
    key: str
    title: str
    summary: str
    resources: List[str]


DEFAULT_LESSONS = [
    Lesson(
        key="variables",
        title="Variables and Types",
        summary="Naming values, primitive types, and basic conversions.",
        resources=["curriculum/python_basics.md#variables-and-types"],
    ),
    Lesson(
        key="control-flow",
        title="Control Flow",
        summary="Conditionals, loops, and truthy/falsey rules.",
        resources=["curriculum/python_basics.md#control-flow"],
    ),
    Lesson(
        key="functions",
        title="Functions",
        summary="Defining and calling functions with parameters and return values.",
        resources=["curriculum/python_basics.md#functions"],
    ),
    Lesson(
        key="collections",
        title="Collections",
        summary="Lists, tuples, sets, dictionaries, and iteration patterns.",
        resources=["curriculum/python_basics.md#collections"],
    ),
    Lesson(
        key="data-analysis",
        title="Intro to Data Analysis",
        summary="Loading, cleaning, summarizing, and visualizing data with pandas.",
        resources=[
            "curriculum/data_analysis.md#getting-started-with-pandas",
            "modules/README.md",
        ],
    ),
]


def load_progress(path: Path) -> Dict:
    if not path.exists():
        return {"completed": [], "notes": {}}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(path: Path, progress: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def list_lessons(lessons: List[Lesson]) -> str:
    lines = ["Available lessons:"]
    for lesson in lessons:
        lines.append(f"- {lesson.key}: {lesson.title} — {lesson.summary}")
    return "\n".join(lines)


def summarize_progress(lessons: List[Lesson], progress: Dict) -> str:
    completed_keys = set(progress.get("completed", []))
    pending = [lesson for lesson in lessons if lesson.key not in completed_keys]

    lines = ["Session summary:"]
    lines.append(f"Completed: {', '.join(sorted(completed_keys)) or 'None yet!'}")
    lines.append(f"Pending: {', '.join(lesson.key for lesson in pending) or 'All done!'}")

    notes = progress.get("notes", {})
    if notes:
        lines.append("Notes:")
        for key, text in notes.items():
            lines.append(f"- {key}: {text}")

    return "\n".join(lines)


def complete_lesson(progress: Dict, lesson_key: str, notes: str | None) -> Dict:
    completed = set(progress.get("completed", []))
    completed.add(lesson_key)
    progress["completed"] = sorted(completed)

    if notes:
        progress.setdefault("notes", {})[lesson_key] = notes

    return progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress-file", type=Path, default=Path("progress.json"), help="Path to the progress JSON file")
    parser.add_argument("--list-lessons", action="store_true", help="List available lessons")
    parser.add_argument("--complete", metavar="LESSON_KEY", help="Mark a lesson as complete")
    parser.add_argument("--notes", help="Notes to attach to the completed lesson")
    parser.add_argument("--summary", action="store_true", help="Print progress summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lessons = DEFAULT_LESSONS

    progress = load_progress(args.progress_file)

    if args.list_lessons:
        print(list_lessons(lessons))

    if args.complete:
        progress = complete_lesson(progress, args.complete, args.notes)
        save_progress(args.progress_file, progress)
        print(f"Marked '{args.complete}' as complete. Progress saved to {args.progress_file}.")

    if args.summary:
        print(summarize_progress(lessons, progress))

    if not any([args.list_lessons, args.complete, args.summary]):
        print("No action requested. Use --list-lessons, --complete, or --summary.")


if __name__ == "__main__":
    main()
