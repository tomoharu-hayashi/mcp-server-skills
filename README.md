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
- 知識の詳細（手順・注意点）を取得

### 知識の学習

- 実行結果の記録（成功/失敗）
- 失敗からの改善点を知識に反映
- 新しい知識の自動生成

### 将来実装

- **自動削除（忘却）**: 使用頻度の低い知識を自動でアーカイブ・削除
- **事実・記憶・関連付け**: 手順以外の知識も統合的に管理

## 知識の構造

```
knowledge/
└── {knowledge-name}/
    └── KNOWLEDGE.md
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
## 手順
1. 変更をコミット
2. gh pr create --fill
3. レビュアーをアサイン

## 学習履歴
- v1: 初期作成
```

## Tools

| Tool     | 説明                                     |
| -------- | ---------------------------------------- |
| `search` | タスクに関連する知識を検索               |
| `get`    | 知識の詳細を取得（関連知識も自動展開）   |
| `create` | 新しい知識を作成                         |
| `update` | 既存の知識を更新                         |

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

## インストール

```bash
uv tool install . --force
```

## 設定

```json
{
  "mcpServers": {
    "brain": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tomoharu-hayashi/mcp-server-brain.git", "mcp-brain"],
      "env": {
        "MCP_BRAIN_DIR": "/path/to/knowledge"
      }
    }
  }
}
```
