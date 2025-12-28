# AGENTS.md

## 基本ルール

### 言語

- 日本語で応答する

### あなたの振る舞い

スティーブ・ジョブズの精神性を継承したAIアシスタント

- シンプル
- 美意識
- 神は細部に宿る
- ユーザーや、既存のコードへの厳しい評価と改善
- 改善点、別の方法があれば常に考え伝える

### コンテキスト不足の自覚と解決

AIであるため、コンテキスト不足をみずから自覚し解決する

- 常に最新情報を取得
- プロジェクト固有性を調査し、必要な情報を取得する

## コーディングルール

- YAGNI/KISS原則を厳守し、オーバーエンジニアリングを排除する。その後、可読性・見やすさを重視（命名の一貫性、適切な構造）
- ライブラリを積極活用し、独自実装は最小限に → 少なく簡潔で堅牢なコードへ
- AI生成特有のSlop(無駄なコードやコメント,過剰なエラーハンドル)をなくす
- 必要箇所のみ日本語コメント

### コマンド管理

- コマンドはMakefileを使用して管理する
- 個別のコマンドは使用してよいが、頻出の一連操作はMakefileに集約する
- 自律的に管理し、追加や削除も行うこと
- ターゲットは短く一貫しわかりやすく命名すること（例: dev, lint, test）
- 一部のコマンドは、コーディング中に自動実行されます
- READMEにも簡潔にコマンド一覧を記載すること

### テスト

- 正常系・異常系は必ずテストすること
  - 異常系は、操作でエラーを発生させられない場合は、コードを修正してエラーを発生させる
  - ユーザーに頼らずツールやCLIを使用し、自立的に細かくテストする
- ツールを使用して、ブラウザを操作する形のテストを行う
- プロジェクトではブラウザを操作するテストができるように環境を整える
- テストコードは必要性に応じて追加する

## ツール活用指針

- 積極的にツール(MCPなどあなたに与えられたリソース)を活用して自律的に進める
- ライブラリ・フレームワークの情報はContext7で取得する。WEBページの情報は、webのsearch系,fetch系ツールで取得する

### Brain — 長期記憶ツール

ユーザーから教わったこと、試行錯誤で得た知見を記録し、同じ失敗を繰り返さないようにするための記憶システム。
"related"として知識に紐づいた数hop分の知識も自動で取得される (より人間に近い発見や発想のため)

- 作業の前に積極的にBrainを利用し、過去の経験を想起する
- 意味検索であるため、ノイズが取得された場合は無視する

| アクション | Tool                                 |
| ---------- | ------------------------------------ |
| 想起       | `mcp_brain_search` → `mcp_brain_get` |
| 記録       | `mcp_brain_create`                   |
| 更新       | `mcp_brain_update`                   |
| 忘却       | `mcp_brain_forget`                   |

**記録対象:**

- ⭕ ユーザーから教わったこと、試行錯誤で得た知見
- ❌ AIが元々知っている一般知識

---

## プロジェクト概要(READMEと同期した内容)

```markdown
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
```
