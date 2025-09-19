# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

from typing import Generator, MutableMapping

from datasets import load_dataset

from utils.prepare_benchmark.common import Task


def gen_futurex_past(hf_token: str) -> Generator[Task, None, None]:
    """
    Generate FutureX-Past dataset tasks in MiroFlow standardized format.

    Args:
        hf_token: Hugging Face token for dataset access (unused here but kept for parity)

    Yields:
        Task: Standardized task objects compatible with the JSONL evaluator
    """
    # Load the FutureX-Past dataset from Hugging Face
    dataset = load_dataset("futurex-ai/FutureX-Past")

    # Iterate through available splits (e.g., train)
    for split_name, split_data in dataset.items():
        for idx, sample in enumerate(split_data):
            # Map required fields
            task_id = sample.get("question_id", f"futurex_past_{split_name}_{idx}")
            task_question = sample.get("prompt") or sample.get("question", "")
            ground_truth = sample.get("answer", "")

            # Build metadata with normalized keys
            end_time = sample.get("end-time", sample.get("setting_time", ""))
            level = sample.get("level", None)
            options = sample.get("options")
            prompt = sample.get("prompt", "")

            metadata: MutableMapping = {
                "end_time": end_time,
                "level": level,
                "options": options,
                "prompt": prompt,
                "source": "futurex-ai/FutureX-Past",
                "split": split_name,
                "original_id": sample.get("question_id", ""),
                "dataset_name": "FutureX-Past",
            }

            if not metadata.get("prompt") and sample.get("question"):
                # Backfill the human-readable question text for reference.
                metadata["question"] = sample.get("question")

            # Create standardized Task object
            task = Task(
                task_id=task_id,
                task_question=task_question,
                ground_truth=ground_truth,
                file_path=None,
                metadata=metadata,
            )

            yield task

    return

