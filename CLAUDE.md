# Claude Code Assistant Configuration

This file contains configuration and notes for Claude Code assistant to help with this codebase.

## Project Overview

MiroFlow is a Python-based benchmark evaluation framework for LLM agents with multi-agent orchestration capabilities. The system supports cost tracking, detailed execution summaries, and comprehensive performance analysis.

## Key Components

### Core Architecture
- **Pipeline (`src/core/pipeline.py`)**: Main execution pipeline for individual tasks
- **Orchestrator (`src/core/orchestrator.py`)**: Coordinates main agent and sub-agent interactions
- **TaskTracer (`src/logging/task_tracer.py`)**: Comprehensive task execution logging and summary generation
- **Cost Tracker (`src/utils/cost_tracker.py`)**: OpenRouter API integration for cost tracking and analysis

### Benchmark System
- **Common Benchmark (`common_benchmark.py`)**: Main benchmark execution framework
- **FutureX Dataset**: Prediction tasks with multiple choice answers
- **Pass@K Evaluation**: Support for multiple attempts per task with early stopping

### Tools and Agents
- **Main Agent**: Primary reasoning agent with tool access
- **Sub-Agents**: Specialized worker agents (e.g., `agent-worker` with file reading capabilities)
- **MCP Integration**: Model Context Protocol for tool communication
- **Tool Servers**: FastMCP servers for various capabilities (reading, web access, etc.)

## Recent Enhancements (2025-09-20)

### 1. Level Filtering for FutureX Benchmark
**Added**: Ability to filter FutureX tasks by difficulty level (1-4)

**Features**:
- `level_filter` parameter in benchmark config
- Runtime level filtering via just commands
- Support for testing specific difficulty levels
- Enhanced filter logic to work alongside existing whitelist filtering

**Usage**:
```bash
just test-10-tasks "model" "futurex-past" "4"  # Test only hardest questions
```

### 2. Fixed Cost Tracking Issues
**Problem**: TaskTracer missing `cost_measurement` field causing runtime errors, and per-task costs showing as $0.000000

**Solution**:
- Added `cost_measurement: dict[str, Any] | None = None` field to TaskTracer
- Enhanced pipeline to pass benchmark cost tracker to task execution
- Fixed cost aggregation in BenchmarkCostTracker

### 3. Enhanced Task Execution Summary
**Added comprehensive summary display including:**
- **Duration**: Execution time in seconds and minutes
- **Main Agent Stats**: Turn count and tool call detection (including MCP tools)
- **Sub-Agent Details**: Session count with per-session turn/message breakdown
- **Cost Analysis**: Total cost and cost per second
- **Step Breakdown**: Chronological execution steps (not alphabetical)
- **Final Answer**: Extracted boxed answer
- **Error Status**: Clear error indication

**Example Output:**
```
============================================================
🎯 TASK EXECUTION SUMMARY - task-123
============================================================
📊 Status: COMPLETED
⏱️  Duration: 230.1s (3.8m)
🤖 Main Agent: 4 turns, 2 tool calls
👥 Sub-Agents: 2 sessions
    └─ agent-worker_1: 3 turns, 7 messages
    └─ agent-worker_2: 3 turns, 7 messages
💰 Cost: $0.003446 ($0.000015/sec)
📝 Step Breakdown:
    └─ search_cutoff_initialized: 1
    └─ get_main_tool_definitions: 1
    └─ main_agent_turn_1_success: 1
    └─ sub_agent-worker_session_start: 2
    └─ sub_agent_tool_call_success: 2
    └─ final_answer: 1
✅ Final Answer: A
============================================================
```

### 4. Improved Tool Call Detection
**Enhanced to detect:**
- Structured `tool_use` objects in message content
- MCP tool calls in string format (`<use_mcp_tool>`)
- Sub-agent invocations through main agent

### 5. Cost Tracking Architecture
**Added complete cost tracking system:**
- OpenRouter API integration for credit monitoring
- Per-task cost measurement with duration tracking
- Benchmark-level cost aggregation
- Enhanced logging with detailed cost breakdowns
- Cost summary JSON export

## Command Reference

### Just Commands
```bash
# Test single task
just test-1-task [model] [dataset] [level]

# Test multiple tasks
just test-10-tasks [model] [dataset] [level]
just test-50-tasks [model] [dataset] [level]

# Run with specific models
just test-1-task "qwen/qwen3-30b-a3b" "futurex-past"

# Test specific difficulty levels (1-4)
just test-10-tasks "qwen/qwen3-30b-a3b" "futurex-past" "4"  # Hardest questions
just test-50-tasks "openai/gpt-4o-mini" "futurex-past" "1"   # Easiest questions

# Prepare dataset
just prepare-data futurex-past
```

### Common Benchmark Usage
```bash
# Run benchmark with cost tracking
uv run main.py common-benchmark \
  --config_file_name=config \
  benchmark=futurex \
  benchmark.data.data_dir=data/futurex-past \
  benchmark.execution.max_tasks=1 \
  main_agent.llm.model_name="qwen/qwen3-30b-a3b" \
  sub_agents.agent-worker.llm.model_name="qwen/qwen3-30b-a3b"
```

## Development Guidelines

### Testing
- Always run `uv run` for Python commands to use proper virtual environment
- Test cost tracking on single tasks before running large benchmarks
- Use `just test-1-task` for quick validation

### Cost Management
- Monitor OpenRouter credits through cost tracker
- Review cost summaries in benchmark output JSON files
- Track per-task costs for performance optimization

### Logging
- Task logs saved to timestamped directories in `logs/`
- Comprehensive execution metadata in TaskTracer JSON files
- Step-by-step execution logging for debugging

### Code Style
- Follow existing patterns for tool integration
- Use proper error handling in cost tracking (never raise in finally blocks)
- Maintain chronological ordering in step logs
- Use descriptive commit messages (1 line, human-readable)

## Troubleshooting

### Common Issues
1. **"TaskTracer has no field cost_measurement"**: Ensure latest TaskTracer with cost_measurement field
2. **Per-task costs showing $0**: Verify benchmark_cost_tracker is passed to execute_task_pipeline
3. **Tool calls showing 0**: Check MCP tool call detection in TaskTracer.generate_summary()
4. **Steps in wrong order**: Ensure chronological ordering preservation in step_breakdown
5. **Rate limiting on OpenRouter**: Switch to less rate-limited models like `openai/gpt-4o-mini` or add your own API keys
6. **"Server 'sports_data' not found"**: Main agent is hallucinating non-existent tool servers - check tool configuration

### OpenRouter Integration
- Requires valid API key in config
- Monitor credit usage through cost tracker
- Handle API rate limits gracefully
- Fallback to local cost estimation if API unavailable

## File Structure Notes

```
src/
├── core/
│   ├── pipeline.py          # Main task execution pipeline
│   └── orchestrator.py      # Agent coordination
├── logging/
│   └── task_tracer.py       # Task execution logging & summaries
├── utils/
│   └── cost_tracker.py      # Cost tracking utilities
└── llm/
    └── client.py            # LLM client implementations

logs/                        # Timestamped execution logs
data/                        # Benchmark datasets
common_benchmark.py          # Main benchmark runner
justfile                     # Command shortcuts
```

## Dependencies

Key dependencies for development:
- `uv` for Python environment management
- `omegaconf` for configuration management
- `pydantic` for data validation
- `requests`/`aiohttp` for API calls
- `fastmcp` for tool protocol
- Jupyter ecosystem for analysis notebooks

## Configuration

### Model Configuration
- OpenRouter API integration for model access
- Support for multiple model providers
- Configurable temperature, top_p, max_tokens
- Per-agent model configuration

### Tool Configuration
- MCP server integration for tool access
- Configurable tool availability per agent type
- Reading tools, web access, and custom tools
- Tool result processing and formatting

## Performance Notes

### Optimization Areas
- Sub-agent session reuse for similar tasks
- Tool call batching where possible
- Cost-efficient model selection
- Parallel task execution with semaphore control

### Monitoring
- Real-time cost tracking during execution
- Step-by-step execution timing
- Tool usage patterns analysis
- Agent interaction efficiency metrics