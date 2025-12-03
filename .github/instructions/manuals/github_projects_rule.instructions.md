---
applyTo: " "
---
<!-- Description: Github Projectsを参照したいときに使用する -->
# Github Projects 管理ルール

## 管理場所

- Projects: [users/tomoharu-hayashi/projects](https://github.com/users/tomoharu-hayashi/projects)
- Issues: [<project_name>/issues](https://github.com/tomoharu-hayashi/<project_name>/issues)

## 運用

- Github Projectsに関する指示を受けたら回答のために積極的に ghコマンドを使用してください
- 追加: Issue を作成（Project は Auto-add を推奨）
- 手動追加が必要な場合のみ:

```bash
gh project item-add <プロジェクト番号> --owner tomoharu-hayashi --url https://github.com/tomoharu-hayashi/<project_name>/issues/<番号>
```

- 進行: Project の Status を To do → In progress → Done に更新
- 完了: Issue を Close

## ラベル（任意）

- `優先度:高` / `優先度:中` / `優先度:低`
