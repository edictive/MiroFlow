# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from typing import Optional, Dict, Any
import requests
import aiohttp
from dataclasses import dataclass
from datetime import datetime

from src.logging.logger import bootstrap_logger
import os

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "INFO")
logger = bootstrap_logger(level=LOGGER_LEVEL)


@dataclass
class CostSnapshot:
    """Represents a snapshot of OpenRouter credits at a point in time."""
    timestamp: datetime
    total_credits: float
    total_usage: float
    remaining_credits: float

    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> "CostSnapshot":
        """Create CostSnapshot from OpenRouter API response."""
        data = response_data.get("data", {})
        total_credits = float(data.get("total_credits", 0))
        total_usage = float(data.get("total_usage", 0))

        return cls(
            timestamp=datetime.now(),
            total_credits=total_credits,
            total_usage=total_usage,
            remaining_credits=total_credits - total_usage
        )


@dataclass
class CostMeasurement:
    """Represents the cost of an operation between two snapshots."""
    start_snapshot: CostSnapshot
    end_snapshot: CostSnapshot
    cost_dollars: float
    duration_seconds: float

    @property
    def cost_per_second(self) -> float:
        """Cost per second during the operation."""
        return self.cost_dollars / self.duration_seconds if self.duration_seconds > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "start_time": self.start_snapshot.timestamp.isoformat(),
            "end_time": self.end_snapshot.timestamp.isoformat(),
            "start_usage": self.start_snapshot.total_usage,
            "end_usage": self.end_snapshot.total_usage,
            "cost_dollars": self.cost_dollars,
            "duration_seconds": self.duration_seconds,
            "cost_per_second": self.cost_per_second,
            "start_remaining_credits": self.start_snapshot.remaining_credits,
            "end_remaining_credits": self.end_snapshot.remaining_credits,
        }


class CostTracker:
    """Tracks costs for OpenRouter API usage."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.credits_endpoint = f"{base_url}/credits"

    def get_credits_sync(self) -> Optional[CostSnapshot]:
        """Get current credits synchronously."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(self.credits_endpoint, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            snapshot = CostSnapshot.from_api_response(data)

            logger.debug(f"Credits snapshot: ${snapshot.remaining_credits:.4f} remaining, ${snapshot.total_usage:.4f} used")
            return snapshot

        except Exception as e:
            logger.warning(f"Failed to get credits: {e}")
            return None

    async def get_credits_async(self) -> Optional[CostSnapshot]:
        """Get current credits asynchronously."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.credits_endpoint, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

            snapshot = CostSnapshot.from_api_response(data)

            logger.debug(f"Credits snapshot: ${snapshot.remaining_credits:.4f} remaining, ${snapshot.total_usage:.4f} used")
            return snapshot

        except Exception as e:
            logger.warning(f"Failed to get credits: {e}")
            return None

    def measure_cost_sync(self, operation_func, *args, **kwargs) -> tuple[Any, Optional[CostMeasurement]]:
        """
        Measure the cost of a synchronous operation.

        Args:
            operation_func: Function to execute and measure
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Tuple of (function_result, cost_measurement)
        """
        start_snapshot = self.get_credits_sync()
        start_time = time.time()

        try:
            result = operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Operation failed during cost measurement: {e}")
            raise

        end_time = time.time()
        end_snapshot = self.get_credits_sync()

        if start_snapshot and end_snapshot:
            cost_dollars = end_snapshot.total_usage - start_snapshot.total_usage
            duration = end_time - start_time

            measurement = CostMeasurement(
                start_snapshot=start_snapshot,
                end_snapshot=end_snapshot,
                cost_dollars=cost_dollars,
                duration_seconds=duration
            )

            logger.info(f"Operation cost: ${cost_dollars:.6f} over {duration:.1f}s")
            return result, measurement
        else:
            logger.warning("Could not measure cost - failed to get credits")
            return result, None

    async def measure_cost_async(self, operation_coro) -> tuple[Any, Optional[CostMeasurement]]:
        """
        Measure the cost of an asynchronous operation.

        Args:
            operation_coro: Coroutine to execute and measure

        Returns:
            Tuple of (coroutine_result, cost_measurement)
        """
        start_snapshot = await self.get_credits_async()
        start_time = time.time()

        try:
            result = await operation_coro
        except Exception as e:
            logger.error(f"Operation failed during cost measurement: {e}")
            raise

        end_time = time.time()
        end_snapshot = await self.get_credits_async()

        if start_snapshot and end_snapshot:
            cost_dollars = end_snapshot.total_usage - start_snapshot.total_usage
            duration = end_time - start_time

            measurement = CostMeasurement(
                start_snapshot=start_snapshot,
                end_snapshot=end_snapshot,
                cost_dollars=cost_dollars,
                duration_seconds=duration
            )

            logger.info(f"Operation cost: ${cost_dollars:.6f} over {duration:.1f}s")
            return result, measurement
        else:
            logger.warning("Could not measure cost - failed to get credits")
            return result, None


class BenchmarkCostTracker:
    """Tracks costs across multiple tasks in a benchmark."""

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.task_costs: Dict[str, CostMeasurement] = {}
        self.benchmark_start_snapshot: Optional[CostSnapshot] = None
        self.benchmark_end_snapshot: Optional[CostSnapshot] = None

    async def start_benchmark(self) -> None:
        """Mark the start of a benchmark run."""
        self.benchmark_start_snapshot = await self.cost_tracker.get_credits_async()
        logger.info("Started benchmark cost tracking")

    async def end_benchmark(self) -> Optional[CostMeasurement]:
        """Mark the end of a benchmark run and calculate total cost."""
        self.benchmark_end_snapshot = await self.cost_tracker.get_credits_async()

        if self.benchmark_start_snapshot and self.benchmark_end_snapshot:
            cost_dollars = self.benchmark_end_snapshot.total_usage - self.benchmark_start_snapshot.total_usage
            duration = (self.benchmark_end_snapshot.timestamp - self.benchmark_start_snapshot.timestamp).total_seconds()

            benchmark_cost = CostMeasurement(
                start_snapshot=self.benchmark_start_snapshot,
                end_snapshot=self.benchmark_end_snapshot,
                cost_dollars=cost_dollars,
                duration_seconds=duration
            )

            logger.info(f"Benchmark total cost: ${cost_dollars:.6f} over {duration:.1f}s")
            logger.info(f"Individual task costs: {len(self.task_costs)} tasks")
            if len(self.task_costs) > 0:
                total_task_cost = sum(task_cost.cost_dollars for task_cost in self.task_costs.values())
                avg_task_cost = total_task_cost / len(self.task_costs)
                logger.info(f"Total task costs: ${total_task_cost:.6f}")
                logger.info(f"Average cost per task: ${avg_task_cost:.6f}")

            return benchmark_cost
        else:
            logger.warning("Could not calculate benchmark cost")
            return None

    def add_task_cost(self, task_id: str, cost_measurement: CostMeasurement) -> None:
        """Add cost measurement for a specific task."""
        self.task_costs[task_id] = cost_measurement
        logger.debug(f"Task {task_id} cost: ${cost_measurement.cost_dollars:.6f}")

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get summary of all costs."""
        task_costs_total = sum(cost.cost_dollars for cost in self.task_costs.values())

        benchmark_cost = None
        if self.benchmark_start_snapshot and self.benchmark_end_snapshot:
            benchmark_cost = self.benchmark_end_snapshot.total_usage - self.benchmark_start_snapshot.total_usage

        return {
            "benchmark_total_cost": benchmark_cost,
            "task_costs_sum": task_costs_total,
            "num_tasks": len(self.task_costs),
            "avg_cost_per_task": task_costs_total / len(self.task_costs) if self.task_costs else 0,
            "task_costs": {task_id: cost.to_dict() for task_id, cost in self.task_costs.items()}
        }


def create_cost_tracker_from_config(config) -> Optional[CostTracker]:
    """Create cost tracker from configuration."""
    try:
        # Get API key from config or environment
        api_key = None
        if hasattr(config, 'main_agent') and hasattr(config.main_agent, 'llm'):
            api_key = getattr(config.main_agent.llm, 'openrouter_api_key', None)

        if not api_key:
            api_key = os.getenv('OPENROUTER_API_KEY')

        if not api_key or api_key == "???":
            logger.warning("No OpenRouter API key found - cost tracking disabled")
            return None

        # Get base URL from config or environment
        base_url = "https://openrouter.ai/api/v1"
        if hasattr(config, 'main_agent') and hasattr(config.main_agent, 'llm'):
            base_url = getattr(config.main_agent.llm, 'openrouter_base_url', base_url)

        if not base_url:
            base_url = os.getenv('OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1")

        cost_tracker = CostTracker(api_key, base_url)
        logger.info("Cost tracking enabled")
        return cost_tracker

    except Exception as e:
        logger.warning(f"Failed to create cost tracker: {e}")
        return None