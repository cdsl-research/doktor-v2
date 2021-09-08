# doktor-v2

This is doktor v2.

## Architecture

<img src="doktor-v2-architecture.png" width="600" alt="doktor-v2 architecture">

## Directory Structure

- `author` 著者を管理するサービス
- `dev_tools` 開発用のツール群
- `front` ユーザが操作するWeb UIのサービス
- `front-admin` 管理者が操作するWeb UIのサービス
- `fulltext` 論文の本文を全文検索するサービス
- `keyword` 分かち書き（文章から単語を抽出）するサービス
- `paper` 論文を管理するサービス
- `stats` アクセス履歴を管理するサービス
- `textize` 論文からテキストに書き起こすサービス
- `thumbnail` 論文に含まれる画像を管理するサービス

## Development Guide

### サービス全体

docker-composeでDocker in Dockerを起動する．

プロジェクトルートで以下を実行する．

```
docker-compose up
```

個々のサービスの`docker-compose`を実行する方法（以下はpaperの場合）

```
docker-compose exec paper-compose docker-compose ps
```

個々のサービスの`docker`を実行する方法（以下はpaperの場合）

```
docker-compose exec paper-dind docker ps
```

### 個別サービス

それぞれのディレクトリに移動して，以下を実行する．

```
docker-compose up --build
```

## Setup for Local Development

以下のパッケージをインストールする．

- Docker for Desktop
- docker-compose
- GNU Make
- Python 3.9 or later
