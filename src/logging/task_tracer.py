# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .logger import bootstrap_logger

import os

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "INFO")
logger = bootstrap_logger(level=LOGGER_LEVEL)


class StepRecord(BaseModel):
    """Record detailed information of task execution steps"""

    step_name: str
    message: str
    timestamp: datetime
    status: Literal["info", "warning", "failed", "success", "debug"] = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskTracer(BaseModel):
    """Only use primitive types, datatime, Path etc."""

    status: Literal["pending", "running", "completed", "interrupted", "failed"] = (
        "pending"
    )

    # task info. hydrated BEFORE task execution.
    task_id: str = ""
    task_name: str = ""
    task_file_name: str | None = ""
    ground_truth: str | None
    input: Any = None

    # not task-related info. hydrated BEFORE task execution.
    log_path: Path

    # profile exeuction time. hydrated AFTER task execution.
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime = Field(default_factory=datetime.now)

    # record task result. hydrdrated AFTER task execution.
    final_boxed_answer: str = ""
    judge_result: str = ""
    error: str = ""
    cost_measurement: dict[str, Any] | None = None

    # record task exection detail. hydrated DURING task_execution.
    current_main_turn_id: int = 0
    current_sub_agent_turn_id: int = 0
    sub_agent_counter: int = 0
    current_sub_agent_session_id: str | None = None
    main_agent_message_history: dict[str, Any] = Field(default_factory=dict)
    sub_agent_message_history_sessions: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )
    step_logs: list[StepRecord] = Field(default_factory=list)

    def start_sub_agent_session(
        self, sub_agent_name: str, subtask_description: str
    ) -> str:
        """Start a new sub-agent session"""
        self.sub_agent_counter += 1
        session_id = f"{sub_agent_name}_{self.sub_agent_counter}"
        self.current_sub_agent_session_id = session_id

        # record sub-agent session start
        self.log_step(
            f"sub_{sub_agent_name}_session_start",
            f"Starting {session_id} for subtask: {subtask_description[:100]}{'...' if len(subtask_description) > 100 else ''}",
            "info",
            metadata={"session_id": session_id, "subtask": subtask_description},
        )

        return session_id

    def end_sub_agent_session(self, sub_agent_name: str):
        """End the current sub-agent session"""
        self.log_step(
            f"sub_{sub_agent_name}_session_end",
            f"Ending {self.current_sub_agent_session_id}",
            "success",
            metadata={"session_id": self.current_sub_agent_session_id},
        )
        self.current_sub_agent_session_id = None
        return None

    def log_step(
        self,
        step_name: str,
        message: str,
        status: Literal["info", "warning", "failed", "success", "debug"] = "info",
        metadata: dict[str, Any] | None = None,
    ):
        """Record execution step"""
        step_log = StepRecord(
            step_name=step_name,
            message=message,
            timestamp=datetime.now(),
            status=status,
            metadata=metadata or {},
        )
        self.step_logs.append(step_log)
        # Also print to console
        logger.debug(f"{step_name}: {message}")

    def generate_summary(self) -> dict[str, Any]:
        """Generate a comprehensive task execution summary."""
        # Calculate total duration
        duration = (self.end_time - self.start_time).total_seconds()

        # Count tool calls from main agent message history
        tool_calls = 0
        main_agent_turns = 0

        if self.main_agent_message_history and "message_history" in self.main_agent_message_history:
            messages = self.main_agent_message_history["message_history"]
            main_agent_turns = len([msg for msg in messages if msg.get("role") == "user"])

            for msg in messages:
                content = msg.get("content", [])

                # Check for structured tool_use objects
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            tool_calls += 1

                # Check for MCP tool calls in string content (like <use_mcp_tool>)
                elif isinstance(content, str):
                    if "<use_mcp_tool>" in content:
                        tool_calls += 1

        # Count sub-agent sessions and their timing
        sub_agent_sessions = len(self.sub_agent_message_history_sessions)
        sub_agent_details = {}

        for session_id, session_data in self.sub_agent_message_history_sessions.items():
            if "message_history" in session_data:
                messages = session_data["message_history"]
                turns = len([msg for msg in messages if msg.get("role") == "user"])
                sub_agent_details[session_id] = {
                    "turns": turns,
                    "messages": len(messages)
                }

        # Analyze step logs for timing breakdown (preserve chronological order)
        step_breakdown = {}
        step_order = []  # Keep track of first occurrence order
        sub_agent_step_times = []

        for step in self.step_logs:
            step_type = step.step_name
            if step_type not in step_breakdown:
                step_breakdown[step_type] = 0
                step_order.append(step_type)  # Track first occurrence
            step_breakdown[step_type] += 1

            # Track sub-agent session timing
            if "sub_" in step_type and ("session_start" in step_type or "session_end" in step_type):
                sub_agent_step_times.append({
                    "step": step_type,
                    "timestamp": step.timestamp,
                    "message": step.message
                })

        # Create ordered step breakdown
        ordered_step_breakdown = {step: step_breakdown[step] for step in step_order}

        # Calculate cost information
        cost_info = {}
        if self.cost_measurement:
            cost_info = {
                "total_cost": self.cost_measurement.get("cost_dollars", 0),
                "cost_per_second": self.cost_measurement.get("cost_dollars", 0) / duration if duration > 0 else 0,
                "duration_seconds": duration
            }

        return {
            "task_execution_summary": {
                "task_id": self.task_id,
                "status": self.status,
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "main_agent": {
                    "turns": main_agent_turns,
                    "tool_calls": tool_calls
                },
                "sub_agents": {
                    "total_sessions": sub_agent_sessions,
                    "session_details": sub_agent_details
                },
                "step_breakdown": ordered_step_breakdown,
                "cost": cost_info,
                "final_answer": self.final_boxed_answer,
                "has_error": bool(self.error)
            }
        }

    def save(self):
        """Persist TaskTracer to disk. used in a finally block, thus never raise Exception."""
        try:
            if not self.log_path.exists():
                self.log_path.parent.mkdir(exist_ok=True, parents=True)
            with open(self.log_path, mode="w") as dest:
                dest.write(self.model_dump_json(indent=2))
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
