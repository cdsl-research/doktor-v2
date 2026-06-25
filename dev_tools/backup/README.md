# backup

VMから `kubectl port-forward` を使って、クラスタ上のMongoDB / Elasticsearch / MinIOをローカルディレクトリにバックアップするスクリプト。

対象は以下の6つ:

| 種別 | namespace | Service | DB/Index/Bucket名 |
|---|---|---|---|
| MongoDB | paper | `paper-mongo` | `paper` |
| MongoDB | author | `author-mongo` | `author` |
| MongoDB | stats | `stats-mongo` | `stats` |
| Elasticsearch | fulltext | `fulltext-elastic` | `fulltext` |
| MinIO | paper | `paper-minio` | `paper` |
| MinIO | thumbnail | `thumbnail-minio` | `thumbnail` |

## 前提条件

VM上に以下がインストール・設定済みであること:

- Bash 4以上
- `kubectl`（対象クラスタにアクセスできるkubeconfigが設定済みであること）
- `mongodump`（[MongoDB Database Tools](https://www.mongodb.com/try/download/database-tools)）
- `elasticdump`（`npm install -g elasticdump`、Node.js/npmが必要）
- `mc`（[MinIO Client](https://min.io/docs/minio/linux/reference/minio-mc.html)）
- `base64` / `gzip` / `grep`（通常のLinux環境には標準で入っている）

## 使い方

```bash
# 6対象すべてをバックアップ（出力先は ./backups/<タイムスタンプ>/）
./backup.sh

# 出力先を指定
./backup.sh --output-dir /var/backups/doktor-v2

# MongoDBだけ、MinIOだけなど対象を絞る
./backup.sh --types mongo
./backup.sh --types minio,elasticsearch

# 実際にはコマンドを実行せず、実行予定の内容だけ確認する
./backup.sh --dry-run
```

実行後、`<output-dir>/<YYYYmmdd_HHMMSS>/` 配下に以下が生成される:

```
mongo/paper-mongo/...        (mongodumpの--gzip出力)
mongo/author-mongo/...
mongo/stats-mongo/...
elasticsearch/fulltext/mapping.json.gz
elasticsearch/fulltext/data.json.gz
minio/paper/...              (mc mirrorによるバケットのミラー)
minio/thumbnail/...
```

## 注意事項

- 各対象は1つずつ順番に処理する（同時に複数のport-forwardは張らない）。
- MongoDB / MinIOの認証情報は実行時に `kubectl get secret` で取得し、平文を保存・ハードコードしない。ログ出力時もマスクする。
- 古いバックアップの自動削除（世代管理）は行わない。必要であれば運用側でcron等と組み合わせて削除すること。
- 失敗した対象があってもスクリプトは継続し、最後にOK/FAILEDのサマリを出力する。1つでも失敗していれば終了コードは1。
