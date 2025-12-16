# Makefile (AI開発向け・汎用・薄いルーター)
# 方針: Makefileは「入口」だけ。重い実体は scripts/ に逃がす。

SHELL := /bin/bash
.DEFAULT_GOAL := help

SCRIPTS_DIR ?= scripts
ARGS ?=
PYTEST_ARGS ?= -n auto --cov
RUFF_ARGS ?= .
PYRIGHT_ARGS ?=

.PHONY: help
help: ## コマンド一覧
	@awk 'BEGIN{FS=":.*##"} /^[a-zA-Z0-9_%-]+:.*##/{printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: doctor
doctor: ## 開発に必要なコマンド/環境のざっくりチェック
	@command -v git >/dev/null || (echo "missing: git" && exit 1)
	@command -v uv >/dev/null || (echo "missing: uv" && exit 1)
	@python -c 'import sys; assert sys.version_info[:2] == (3, 13), sys.version' >/dev/null
	@echo "ok: basic"

.PHONY: deps
deps: ## 依存導入（dev含む）
	@uv sync --group dev

.PHONY: dev
dev: ## 開発起動（mcp-brain）
	@uv run mcp-brain $(ARGS)

.PHONY: run
run: dev ## dev の別名

.PHONY: test
test: ## テスト
	@uv run python -m pytest $(PYTEST_ARGS)

.PHONY: fmt
fmt: ## フォーマット
	@uv run ruff check --fix $(RUFF_ARGS)
	@uv run ruff format $(RUFF_ARGS)

.PHONY: lint
lint: ## リント/静的解析
	@uv run ruff format --check $(RUFF_ARGS)
	@uv run ruff check $(RUFF_ARGS)
	@uv run python -m pyright $(PYRIGHT_ARGS)

.PHONY: check
check: lint test ## lint + test

.PHONY: clean
clean: ## 生成物削除
	@rm -rf .tmp .cache dist build coverage 2>/dev/null || true

# ---- プロジェクト固有の新規コマンド（この下に追加）----
# Example:
# .PHONY: install-api-client
# install-api-client: 
# 	@echo "TODO: implement install-api-client"
# ...
# .PHONY: build
# build: 
# 	@echo "TODO: implement build"
# ...


# ---- 実体（コマンドが10行以上の場合 scripts/ に逃がす）----
.PHONY: scripts/%
scripts/%: ## scripts/<name> を実行: make scripts/foo
	@bash "$(SCRIPTS_DIR)/$*"

 
