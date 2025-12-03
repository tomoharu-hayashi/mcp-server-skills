---
applyTo: "**"
---

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

## スコープとフィルタリング

### スコープの階層構造

知識は**プロジェクトスコープ**で管理され、階層的に検索されます。

```
/Users/you/
├── pj/
│   ├── work/
│   │   └── api-server/     ← プロジェクトA
│   └── personal/
│       └── blog/           ← プロジェクトB
└── .mcp-brain/
    ├── global/                              ← 全プロジェクトから見える
    ├── Users/you/pj/work/                   ← work以下のプロジェクトから見える
    └── Users/you/pj/work/api-server/        ← api-serverのみから見える
```

### 優先度とフィルタリング

プロジェクトAから知識を検索すると、以下の順で検索されます:

1. `Users/you/pj/work/api-server/` (最優先)
2. `Users/you/pj/work/`
3. `Users/you/pj/`
4. `Users/you/`
5. `global` (最低優先度)

**重要な特性**:

- ✅ **同名の知識**: より具体的なスコープが優先される
- ✅ **兄弟プロジェクトの除外**: プロジェクトBの知識は見えない
- ✅ **親スコープの継承**: 親ディレクトリの知識は全て見える
- ✅ **globalの共有**: globalの知識は全プロジェクトから見える

### 使い分けの例

| スコープ | 用途 | 例 |
|---------|------|-----|
| **プロジェクト固有** | そのプロジェクト専用の手順 | `deploy-api-server`: API固有のデプロイ手順 |
| **親ディレクトリ** | 同じ組織/チーム共通の手順 | `code-review-process`: チームのレビュールール |
| **global** | 全プロジェクト共通の汎用的な知識 | `git-rebase`: 一般的なGit操作 |

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
