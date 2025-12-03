# Embeddingインデックス仕様

## 概要

MCP Brain Serverは起動時にEmbeddingインデックスを構築する。
起動高速化のため、キャッシュ機構を実装し、変更がなければ再計算を省略する。

## 設計思想

**シンプルさと堅牢性を優先**

- 同期ビルドのみ（バックグラウンド処理なし）
- 競合状態が構造的に発生しない
- 外部からの変更に自動対応

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         起動フロー                               │
├─────────────────────────────────────────────────────────────────┤
│  main()                                                         │
│    ├─ KnowledgeStorage初期化                                    │
│    ├─ SemanticSearch初期化 (cache_dir指定)                      │
│    └─ search_engine.build(items)                                │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ EmbeddingIndex.build()                                    │  │
│  │   ├─ キャッシュチェック                                   │  │
│  │   │   ├─ 有効 → キャッシュ読込 → 即座に起動完了          │  │
│  │   │   └─ 無効 → 同期ビルド → キャッシュ保存              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## キャッシュファイル

知識ディレクトリ（デフォルト: `~/.mcp-brain`）に以下のファイルが生成される:

| ファイル | 内容 |
|---------|------|
| `.index_cache.pkl` | Embeddingベクトルの辞書（pickle形式） |
| `.index_hash` | 知識ファイル群のSHA256ハッシュ |

## キャッシュ有効性判定

### ハッシュ計算ロジック

```python
def compute_content_hash(knowledge_dir: Path) -> str:
    """知識ディレクトリの内容からハッシュを計算"""
    hasher = hashlib.sha256()
    
    # 全KNOWLEDGE.mdファイルを取得（ソート済み）
    knowledge_files = sorted(knowledge_dir.rglob("KNOWLEDGE.md"))
    
    for f in knowledge_files:
        # 相対パスと内容をハッシュに含める
        hasher.update(str(f.relative_to(knowledge_dir)).encode())
        hasher.update(f.read_bytes())
    
    return hasher.hexdigest()
```

### 有効性チェック（load時に統合）

`load()` メソッドが以下をチェックし、無効なら `None` を返す:

1. `.index_cache.pkl` が存在する
2. `.index_hash` が存在する
3. 保存されたハッシュ == 現在のハッシュ

無効化されるケース:

- 知識ファイル（`KNOWLEDGE.md`）の内容変更
- 知識ファイルの追加・削除
- 知識ファイルのパス変更

## 外部変更への耐性

### ユーザーによる手動編集

ユーザーがエディタで直接 `KNOWLEDGE.md` を編集した場合:

1. 次回起動時にハッシュが不一致
2. キャッシュが自動的に無効化
3. 新しい内容でインデックス再構築

**手動編集は常に安全に反映される。**

### Git操作による変更

`git pull`, `git checkout`, `git reset` などでファイルが変更された場合も同様:

1. ファイル内容が変わればハッシュが変化
2. キャッシュ無効化 → 再構築

**Gitによる同期は自動的にインデックスに反映される。**

### キャッシュ破損

pickle読み込み失敗時は `None` を返し、再構築が走る。
アトミック書き込みにより、書き込み中のクラッシュでも破損しない。

## アトミックな書き込み

キャッシュ破損を防ぐため、一時ファイル + `rename` でアトミック化:

```python
def save(self, embeddings: dict[str, np.ndarray]) -> None:
    # 一時ファイルに書いてからrenameでアトミック化
    tmp_cache = self.cache_path.with_suffix(".tmp")
    with tmp_cache.open("wb") as f:
        pickle.dump(embeddings, f)
    tmp_cache.rename(self.cache_path)
    
    tmp_hash = self.hash_path.with_suffix(".tmp")
    tmp_hash.write_text(current_hash)
    tmp_hash.rename(self.hash_path)
```

## 動的インデックス更新

知識の追加・更新・削除時はインデックスを動的に更新し、キャッシュも同期する。

### 追加 (`add`)

```python
def add(self, knowledge: Knowledge) -> None:
    self._load_model()
    text = self._knowledge_to_text(knowledge)
    vector = self.model.encode(PASSAGE_PREFIX + text)
    self.embeddings[knowledge.name] = vector
    self._save_cache()
```

### 更新 (`update`)

更新は追加と同じ処理（上書き）。

### 削除 (`remove`)

```python
def remove(self, name: str) -> None:
    self.embeddings.pop(name, None)
    self.knowledge_texts.pop(name, None)
    self._save_cache()
```

## パフォーマンス特性

| シナリオ | 起動時間 | 検索可能まで |
|---------|---------|-------------|
| キャッシュあり | 数百ms | 即座 |
| キャッシュなし | 3-5秒 | 起動完了と同時 |

## 使用モデル

- デフォルト: `cl-nagoya/ruri-v3-30m`
- 日本語に特化した小型Embeddingモデル
- クエリには `クエリ:` プレフィックス、文章には `文章:` プレフィックスを付与
