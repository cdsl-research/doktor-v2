# doktor-v2

This is doktor v2.

## Architecture

<img src="doktor-v2-architecture.png" width="600" alt="doktor-v2 architecture">

## For Developer

When you contribute to doktor-v2, you need to read [Developer Guide](./DEVELOP_GUIDE.md).

## Branch Policy

- `master`
  - Latest and Stable release
  - 開発したコードはここへマージ
- `staging`
  - Staging release (equal to staging environment)
  - 手元（ローカル）で動作検証を行った後にPull Requestをmasterからstagingへ作成
  - http://doktor-prod1:30200/
- `production` 
  - Production release (equal to production environment)
  - stagingで動作検証を行った後にPull Requestをmasterからproductionへ作成
  - https://doktor.tak-cslab.org/

## Directory Structure

構成ファイル・スクリプト

- `deploy` デプロイ用の構成ファイル
- `dev_tools` 開発用のツール群

各サービス

- `author` 著者を管理するサービス
- `front` ユーザが操作するWeb UIのサービス
- `front-admin` 管理者が操作するWeb UIのサービス
- `fulltext` 論文の本文を全文検索するサービス
- `keyword` 分かち書き（文章から単語を抽出）するサービス
- `paper` 論文を管理するサービス
- `stats` アクセス履歴を管理するサービス
- `textize` 論文からテキストに書き起こすサービス
- `thumbnail` 論文に含まれる画像を管理するサービス

