# Makefile (AI開発向け・汎用・薄いルーター)
# 方針: Makefileは「入口」だけ。重い実体は scripts/ に逃がす。
# スクリプト配置:
#   - .prompts/scripts/  : テンプレートリポジトリから提供（pr-review, pr-checks-wait等）
#   - scripts/           : プロジェクト固有（この下に追加）

SHELL := /bin/bash
.DEFAULT_GOAL := help

SCRIPTS_DIR ?= scripts
PR ?= $(shell gh pr view --json number --jq .number 2>/dev/null)

.PHONY: help
help: ## コマンド一覧
	@awk 'BEGIN{FS=":.*##"} /^[a-zA-Z0-9_%-]+:.*##/{printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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
	@find . -path "./.git" -prune -o -name ".DS_Store" -type f -delete
	@find . -path "./.git" -prune -o -type d -empty -delete

.PHONY: pr-review
pr-review: ## PRのレビュー/コメントを全取得
	@bash ".prompts/scripts/pr_review.sh"

.PHONY: pr-checks-wait
pr-checks-wait: ## PRのCIチェックをポーリング（TIMEOUT秒で打ち切り、デフォルト: 1800）
	@bash ".prompts/scripts/pr_checks_wait.sh"

.PHONY: pr-merge
pr-merge: ## PRを即時マージ
	@test -n "$(PR)" || (echo "PR not found. Set PR=<number> or checkout a PR branch." && exit 1)
	@gh pr merge "$(PR)" --squash

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

 
