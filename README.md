# MCP Brain Server

AIエージェントに「統合的な知識」を提供するMCPサーバー

## コンセプト

**人間が仕事を覚えるように、AIも知識を学習する**

人間が仕事を習得するプロセス:

1. **観察**: 先輩のやり方を見る
2. **実践**: 自分でやってみる
3. **失敗**: うまくいかない
4. **修正**: フィードバックを受けて調整
5. **定着**: 繰り返して身につく

このサーバーは、AIエージェントに同様の学習サイクルを提供する。

## 機能

### 知識の参照

- タスクに関連する知識を検索
- 知識の詳細を取得

### 知識の学習

- 実行結果の記録（成功/失敗）
- 失敗からの改善点を知識に反映
- 新しい知識の自動生成

### 将来実装

- **自動削除（忘却）**: 使用頻度の低い知識を自動でアーカイブ・削除

## 知識の構造

```
mcp-brain-storage/          # Gitリポジトリ（Obsidianで開ける）
├── .index_cache.pkl        # キャッシュ
├── .index_hash
├── README.md
└── knowledge/              # 知識ファイルはここに配置
    ├── create-pr.md        # フラット形式（Obsidian互換）
    ├── deploy-staging.md
    └── git-commit.md
```

```yaml
---
name: create-pr
description: PRを作成したいとき
version: 1
created: 2025-12-01
---
```

```markdown
PRを作成する方法。

1. 変更をコミット
2. gh pr create --fill
3. レビュアーをアサイン
```

## Tools

| Tool     | 説明                                   |
| -------- | -------------------------------------- |
| `search` | タスクに関連する知識を検索             |
| `get`    | 知識の詳細を取得（関連知識も自動展開） |
| `create` | 新しい知識を作成                       |
| `update` | 既存の知識を更新                       |

### 関連知識の自動連想

`get` で知識を取得すると、**Embeddingベースの類似度**で関連する知識が自動的に展開されます。
手動でリンクを張る必要はありません。脳のように、意味的に近い知識が自動で連想されます。

`hops` パラメータで連想の深さを指定可能（デフォルト: 2）。

```python
# 2ホップ先まで関連知識を取得
get(name="create-pr", hops=2)
```

```json
{
  "name": "create-pr",
  "description": "PRを作成したいとき",
  "content": "## 手順...",
  "related": [
    {
      "name": "git-commit",
      "description": "変更をコミットしたいとき",
      "related": [
        {"name": "git-push", "description": "リモートにプッシュしたいとき", "related": []}
      ]
    }
  ]
}
```

## Git連携

### 自動バージョン管理

知識の作成・更新・削除は**自動的にGitにコミット**されます。

```bash
# 知識ディレクトリをGitリポジトリとして初期化
cd ~/.mcp-brain
git init
git remote add origin git@github.com:your-name/mcp-brain-knowledge.git

# 以降、知識の変更は自動でコミット・プッシュされる
```

### コミットメッセージ

操作に応じて自動生成されます:

- `create: {knowledge-name}` - 新しい知識を作成
- `update: {knowledge-name}` - 既存の知識を更新
- `forget: {knowledge-name}` - 知識を削除

### メリット

- 📝 **履歴管理**: 知識の変更履歴を追跡
- 🔄 **同期**: 複数デバイス間で知識を同期
- 👥 **共有**: チームで知識を共有
- 🔙 **復元**: 削除した知識を復元可能

## インストール

```bash
uv tool install . --force
```

## 開発コマンド

```bash
make help
make doctor
make deps
make lint
make fmt
make test
make dev ARGS="--help"
```

## 設定

### 共通知識（全プロジェクトで共有）

```json
{
  "mcpServers": {
    "brain": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tomoharu-hayashi/mcp-server-brain.git", "mcp-brain"],
      "env": {
        "MCP_BRAIN_DIR": "~/pj/my/mcp-brain-storage"
      }
    }
  }
}
```

### プロジェクト独立の知識

プロジェクトごとに完全に独立した知識空間を持たせる場合。

#### 1. プロジェクト内に知識ディレクトリを作成

```bash
cd /path/to/your-project
mkdir .brain
cd .brain
git init
git remote add origin git@github.com:your-name/your-project-brain.git
```

#### 2. MCP設定（プロジェクトごと）

VS Code / Cursor の場合、`.vscode/mcp.json` を作成:

```json
{
  "mcpServers": {
    "brain": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tomoharu-hayashi/mcp-server-brain.git", "mcp-brain"],
      "env": {
        "MCP_BRAIN_DIR": "${workspaceFolder}/.brain"
      }
    }
  }
}
```

#### 3. .gitignore に追加

親リポジトリで `.brain/` が検知されないように:

```gitignore
.brain/
```

### 構成パターン

| パターン         | MCP_BRAIN_DIR               | 用途                                |
| ---------------- | --------------------------- | ----------------------------------- |
| 共通             | `~/pj/my/mcp-brain-storage` | 汎用ワークフロー（Git、PR作成など） |
| プロジェクト独立 | `${workspaceFolder}/.brain` | プロジェクト固有の知識              |
| チーム共有       | リポジトリ内 `.brain/`      | チームで知識を共有                  |
