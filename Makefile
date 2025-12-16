# Makefile (AI開発向け・汎用・薄いルーター)
# 方針: Makefileは「入口」だけ。重い実体は scripts/ に逃がす。

SHELL := /bin/bash
.DEFAULT_GOAL := help

SCRIPTS_DIR ?= scripts

.PHONY: help
help: ## コマンド一覧
	@awk 'BEGIN{FS=":.*##"} /^[a-zA-Z0-9_%-]+:.*##/{printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: doctor
doctor: ## 開発に必要なコマンド/環境のざっくりチェック
	@command -v git >/dev/null || (echo "missing: git" && exit 1)
	@echo "ok: basic"

.PHONY: deps
deps: ## 依存導入（PJに合わせて実装）
	@echo "TODO: implement deps"

.PHONY: run
run: ## 実行（dev起動など）
	@echo "TODO: implement run"

.PHONY: test
test: ## テスト
	@echo "implement test"

.PHONY: fmt
fmt: ## フォーマット
	@echo "TODO: implement fmt"

.PHONY: lint
lint: ## リント/静的解析
	@echo "TODO: implement lint"

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

 
