export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research data/sample/build.py
	$(UV) run ruff format --check src tests research data/sample/build.py
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py

eval:
	$(UV) run python research/phase0/signal_quality/run.py
	$(UV) run python research/phase0/label_availability/run.py
	$(UV) run python research/phase0/pkpd_validation/run.py
	$(UV) run python research/phase0/operating_point/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	@echo "=== or-signals inspect clean ==="
	$(UV) run or-signals inspect --case 'data/sample/clean.*'
	@echo
	@echo "=== or-signals quality artifact --report ==="
	$(UV) run or-signals quality --case 'data/sample/artifact.*' --report
	@echo
	@echo "=== or-signals quality dropout ==="
	$(UV) run or-signals quality --case 'data/sample/dropout.*'
	@echo
	@echo "=== or-signals pkpd bolus --plot ==="
	$(UV) run or-signals pkpd --case 'data/sample/bolus.*' --plot

record:
	$(UV) run python scripts/record_casts.py
