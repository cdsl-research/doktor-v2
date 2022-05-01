# 開発ガイド

## 環境

- Docker for Desktop 4.1.1
- docker-compose v2.0.0
- Python 3.9 or later

## 開発環境の構築(初回のみ)

プロジェクトのルートディレクトリに移動する．

```shell
$ pwd
/path/to/doktor-v2
```

Docker Networkを作成する．

```shell
docker network create frontend
```

[Runner](https://github.com/stylemistake/runner#installation)をインストールする．

```
npm install -g bash-task-runner
```

## 開発環境の起動

プロジェクトのルートディレクトリに移動する．

```shell
$ pwd
/path/to/doktor-v2
```

Runnerでdocker-composeをまとめて起動する．

```shell
runner up
```

ブラウザで以下のURLへアクセスする．

- Web UI(front) http://localhost:4000/
- Admin UI(front-admin) http://localhost:4300/

停止する場合は以下のコマンドを実行する．

```shell
runner down
```