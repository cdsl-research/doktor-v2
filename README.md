# doktor-v2

マイクロサービスアーキテクチャで設計された論文検索サイトです．

## アーキテクチャ

Kubernetesクラスタ上にデプロイする設計です．サービスメッシュにはIstioを利用しています．

<img src="intro-doktor-v2.png" width="600" alt="doktor-v2 architecture">

## 開発者向け

開発にJOINする場合は，[Developer Guide](./DEVELOP_GUIDE.md)を参照ください．

個々のサービスはコンテナ化されています．それぞれのサービスのAPIドキュメントは以下から参照できます．

https://cdsl-research.github.io/doktor-v2/

## ブランチポリシー

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

