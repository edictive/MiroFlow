default:
    just --list

# lint monorepo
[group('precommit')]
lint:
    uv tool run ruff@0.8.0 check --fix .

# format monorepo
[group('precommit')]
format:
    uv tool run ruff@0.8.0 format .

# run test in local package
[group('precommit')]
pytest:
    uv sync --directory {{invocation_directory()}} --group dev
    uv run --directory {{invocation_directory()}} pytest tests

# check license
[group('precommit')]
check-license:
    uv run reuse lint

# insert license for contributor
insert-license:
    # https://reuse.readthedocs.io/en/stable/scripts.html#add-headers-to-staged-files-based-on-git-settings
    git diff --name-only --cached | xargs -I {} reuse annotate -c "$(git config --get user.name) <$(git config --get user.email)>" "{}"

# run precommit before PR
[group('precommit')]
precommit: lint format pytest check-license

# prepare futurex datasets
[group('data')]
prepare-data dataset="futurex-past":
    uv run main.py prepare-benchmark get {{dataset}}

# test single task with specified model and dataset
[group('test')]
test-1-task model="qwen/qwen3-30b-a3b" dataset="futurex-past" level="null":
    uv run main.py common-benchmark \
      --config_file_name=config \
      benchmark=futurex \
      benchmark.data.data_dir=data/{{dataset}} \
      benchmark.execution.max_tasks=1 \
      benchmark.data.level_filter={{level}} \
      main_agent.llm.model_name="{{model}}" \
      sub_agents.agent-worker.llm.model_name="{{model}}" \
      output_dir="logs/{{dataset}}-test1/$(date +%Y%m%d_%H%M%S)"

# test 10 tasks with specified model and dataset
[group('test')]
test-10-tasks model="qwen/qwen3-30b-a3b" dataset="futurex-past" level="null":
    uv run main.py common-benchmark \
      --config_file_name=config \
      benchmark=futurex \
      benchmark.data.data_dir=data/{{dataset}} \
      benchmark.execution.max_tasks=10 \
      benchmark.data.level_filter={{level}} \
      main_agent.llm.model_name="{{model}}" \
      sub_agents.agent-worker.llm.model_name="{{model}}" \
      output_dir="logs/{{dataset}}-test10/$(date +%Y%m%d_%H%M%S)"

# test 50 tasks with specified model and dataset
[group('test')]
test-50-tasks model="qwen/qwen3-30b-a3b" dataset="futurex-past" level="null":
    uv run main.py common-benchmark \
      --config_file_name=config \
      benchmark=futurex \
      benchmark.data.data_dir=data/{{dataset}} \
      benchmark.execution.max_tasks=50 \
      benchmark.data.level_filter={{level}} \
      main_agent.llm.model_name="{{model}}" \
      sub_agents.agent-worker.llm.model_name="{{model}}" \
      output_dir="logs/{{dataset}}-test50/$(date +%Y%m%d_%H%M%S)"