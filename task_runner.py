from __future__ import annotations

"""Utility to run multiple JARVIS tasks serially or in parallel."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List

from core.orchestrator import Orchestrator


class TaskRunner:
    """Run a series of queries autonomously with the Orchestrator."""

    def __init__(self, workers: int = 4) -> None:
        self.workers = max(1, workers)

    def run_serial(self, tasks: Iterable[str]) -> List[str]:
        orchestrator = Orchestrator()
        results: List[str] = []
        for task in tasks:
            results.append(orchestrator.chat(task))
        return results

    def run_parallel(self, tasks: Iterable[str]) -> List[str]:
        tasks = list(tasks)
        results: List[str] = ["" for _ in tasks]

        def _run(index: int, query: str) -> tuple[int, str]:
            orchestrator = Orchestrator()
            return index, orchestrator.chat(query)

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(_run, i, t): i for i, t in enumerate(tasks)}
            for future in as_completed(futures):
                idx, output = future.result()
                results[idx] = output
        return results


def load_tasks_from_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run JARVIS autonomously on a list of tasks"
    )
    parser.add_argument("--tasks", nargs="*", help="Tasks to process")
    parser.add_argument("--tasks-file", help="File containing tasks, one per line")
    parser.add_argument("--parallel", action="store_true", help="Run tasks in parallel")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    args = parser.parse_args()

    tasks: List[str] = []
    if args.tasks_file:
        tasks.extend(load_tasks_from_file(args.tasks_file))
    if args.tasks:
        tasks.extend(args.tasks)

    if not tasks:
        parser.error("No tasks provided via --tasks or --tasks-file")

    runner = TaskRunner(workers=args.workers)
    if args.parallel:
        results = runner.run_parallel(tasks)
    else:
        results = runner.run_serial(tasks)

    for task, result in zip(tasks, results):
        print(f"TASK: {task}\nRESULT: {result}\n")


if __name__ == "__main__":
    main()

