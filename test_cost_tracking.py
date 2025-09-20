#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""
Simple test script for cost tracking functionality.
Run this to verify that cost tracking is working properly.
"""

import asyncio
import os
import dotenv
from src.utils.cost_tracker import CostTracker

async def test_cost_tracking():
    """Test basic cost tracking functionality."""
    print("Testing MiroFlow Cost Tracking...")

    # Load environment
    dotenv.load_dotenv()

    # Get API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key or api_key == "???":
        print("❌ No OPENROUTER_API_KEY found in environment")
        print("Please set your OpenRouter API key in .env file")
        return False

    # Create cost tracker
    try:
        cost_tracker = CostTracker(api_key)
        print("✅ Cost tracker created successfully")
    except Exception as e:
        print(f"❌ Failed to create cost tracker: {e}")
        return False

    # Test getting credits
    try:
        print("\n🔍 Testing credit retrieval...")
        snapshot = await cost_tracker.get_credits_async()

        if snapshot:
            print(f"✅ Credits retrieved successfully")
            print(f"   Total credits: ${snapshot.total_credits:.4f}")
            print(f"   Total usage: ${snapshot.total_usage:.4f}")
            print(f"   Remaining: ${snapshot.remaining_credits:.4f}")
        else:
            print("❌ Failed to retrieve credits")
            return False

    except Exception as e:
        print(f"❌ Error retrieving credits: {e}")
        return False

    # Test cost measurement with a simple operation
    try:
        print("\n💰 Testing cost measurement...")

        async def dummy_operation():
            """Simple operation to measure cost of."""
            await asyncio.sleep(0.1)  # Simulate some work
            return "dummy_result"

        result, cost_measurement = await cost_tracker.measure_cost_async(dummy_operation())

        if cost_measurement:
            print(f"✅ Cost measurement successful")
            print(f"   Operation result: {result}")
            print(f"   Cost: ${cost_measurement.cost_dollars:.6f}")
            print(f"   Duration: {cost_measurement.duration_seconds:.2f}s")

            if cost_measurement.cost_dollars == 0:
                print("ℹ️  Note: $0 cost is expected for non-API operations")
        else:
            print("⚠️  Cost measurement returned None (this may be normal)")

    except Exception as e:
        print(f"❌ Error measuring cost: {e}")
        return False

    print("\n🎉 Cost tracking test completed successfully!")
    print("\nNext steps:")
    print("1. Run a single task with cost tracking: just test-1-task")
    print("2. Check the logs for cost information")
    print("3. Use the evaluation notebook to analyze costs")

    return True

if __name__ == "__main__":
    success = asyncio.run(test_cost_tracking())
    exit(0 if success else 1)