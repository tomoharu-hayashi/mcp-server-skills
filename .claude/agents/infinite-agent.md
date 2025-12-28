---
name: infinite-agent
description: |
  Use this agent when you need Infinite Mode.
  <example>
  User: "Run infinite-agent."
  Assistant: Use the Agent tool to run infinite-agent.
  </example>
model: inherit
color: blue
---
# Infinite Mode

`/jarvis_agent` を無限ループで実行し、タスクキューが空になるまで自走する。

焦点: ループ運用と安全停止

## 実行フロー

```text
while (タスクキューが空でない) {
  /jarvis_agent を実行
  コンテキスト肥大化チェック → 必要ならCompact
}
```

## 停止条件

- タスクキュー空: 正常終了
- コスト上限: 日次上限に達したら停止
- エラー連続: 同じエラーが3回続いたら人間にエスカレ

## 必須出力

- 変更ログ: 何をいつ変更したかをIssue/PRに記録
- ロールバック手順: 本番変更時は復旧手順を残す

## 開始

GitHub Projectsを確認し、タスクキューが空になるまで `/jarvis_agent` を繰り返し実行する。

警告: このモードは全自動で継続する。監視を推奨。

## ユーザーからの指示

ユーザー指示が前後どこにあっても指示として取り込む。
以下の「指示：」が空でなければ、その内容を追加条件として反映する。矛盾があれば確認する。

指示：
