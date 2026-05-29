---
name: bump-version
description: doktor-v2 のサービス（front, front-admin, author, paper, fulltext, thumbnail, stats）のコードを変更したら、該当サービスの VERSION ファイルを必ずバンプする手順。CI が既存タグと衝突するとビルドを失敗させるため必須。
---

# サービスのバージョンをあげる (bump-version)

doktor-v2 の各サービスは `<service>/VERSION` ファイルがコンテナイメージタグの
single source of truth になっている。サービスのコードを変更したら、この VERSION を
**必ずバンプ（インクリメント）すること**。

## なぜ必須か

`.github/workflows/image-build.yml` の "Read version and fail if tag already exists"
ステップで、`ghcr.io/cdsl-research/<service>:<VERSION>` が既に存在すると
`exit 1` でビルドが失敗する。したがって VERSION を上げ忘れると master へ
push した CI が落ちる。

## 対象サービス

`author` / `front` / `front-admin` / `paper` / `fulltext` / `thumbnail` / `stats`

（CI の detect-changes ジョブが監視している一覧と一致させること）

## 手順

1. 変更したサービスの `<service>/VERSION` を開く。
2. セマンティックバージョニングに従ってバンプする。
   - バグ修正・小さな UI 調整 → patch を上げる（例: `2.0` → `2.0.1`）
   - 後方互換のある機能追加 → minor を上げる（例: `2.0.1` → `2.1.0`）
   - 破壊的変更 → major を上げる（例: `2.1.0` → `3.0.0`）
3. `deploy/**` の image タグは**手で書き換えない**。
   master マージ後に CI（k8s-config-update ジョブ）が `sed` で自動更新し、
   "Kubernetes config update" PR を作成する。

## やってはいけないこと

- VERSION を据え置いたままサービスのコードだけ変更して master に push する
  （CI が失敗する）。
- `deploy/<service>/*.yml` の image タグを手動で書き換える
  （CI の自動更新と競合する）。

## 例: front を patch バンプ

```
# front/VERSION
2.0   →   2.0.1
```

これだけで OK。デプロイ設定の追従は CI に任せる。
