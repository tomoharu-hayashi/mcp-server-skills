# MCP Skills Server

AIエージェントに「学習可能なスキル」を提供するMCPサーバー

## コンセプト

**人間が仕事を覚えるように、AIもスキルを学習する**

人間が仕事を習得するプロセス:

1. **観察**: 先輩のやり方を見る
2. **実践**: 自分でやってみる
3. **失敗**: うまくいかない
4. **修正**: フィードバックを受けて調整
5. **定着**: 繰り返して身につく

このサーバーは、AIエージェントに同様の学習サイクルを提供する。

## 機能

### スキルの参照

- タスクに関連するスキルを検索
- スキルの詳細（手順・注意点）を取得
- Claude Code Agent Skills形式と互換

### スキルの学習

- 実行結果の記録（成功/失敗）
- 失敗からの改善点をスキルに反映
- 新しいスキルの自動生成

### 将来実装

- **セマンティック検索**: キーワードではなく意味でスキルを検索（人間の連想に近い）
- **自動削除（忘却）**: 使用頻度の低いスキルを自動でアーカイブ・削除

## スキルの構造

```
skills/
└── {skill-name}/
    └── SKILL.md
```

```yaml
---
name: create-pr
version: 1
created: 2025-12-01
success_count: 0
failure_count: 0
---
```

```markdown
## いつ使う
PRを作成したいとき

## 手順
1. 変更をコミット
2. gh pr create --fill
3. レビュアーをアサイン

## 学習履歴
- v1: 初期作成
```

## Tools

| Tool | 説明 |
|------|------|
| `search_skills` | タスクに関連するスキルを検索 |
| `get_skill` | スキルの詳細を取得 |
| `create_skill` | 新しいスキルを作成 |
| `update_skill` | 既存スキルを更新 |
| `record_execution` | 実行結果を記録 |

## インストール

```bash
uv tool install . --force
```

## 設定

```json
{
  "mcpServers": {
    "skills": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tomoharu-hayashi/mcp-server-skills.git", "mcp-server-skills"],
      "env": {
        "MCP_SKILLS_DIR": "/path/to/skills"
      }
    }
  }
}
```
