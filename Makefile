UV ?= uv
HOST ?=
PORT ?=
TIMEOUT ?= 10

SERVE_ARGS = $(if $(HOST),--host $(HOST)) $(if $(PORT),--port $(PORT))

.PHONY: help install sync run serve scan dump test lint format format-check typecheck check build

help:
	@printf '%s\n' \
		'make install       Install project and development dependencies' \
		'make run           Run the local server' \
		'make scan          Scan BLE devices once' \
		'make dump          Capture repeated T9146 BLE payloads' \
		'make test          Run tests' \
		'make lint          Run Ruff checks' \
		'make format        Fix lint issues and format code' \
		'make format-check  Check formatting without changes' \
		'make typecheck     Run Pyright' \
		'make check         Run all quality checks and tests' \
		'make build         Build wheel and source distribution'

install sync:
	$(UV) sync

run serve:
	$(UV) run eufylocal serve $(SERVE_ARGS)

scan:
	$(UV) run eufylocal scan --timeout $(TIMEOUT)

dump:
	$(UV) run eufylocal dump --timeout $(TIMEOUT)

test:
	$(UV) run pytest -q

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

format-check:
	$(UV) run ruff format --check .

typecheck:
	$(UV) run pyright

check: lint format-check typecheck test

build:
	$(UV) build
