# sample-data-uploader

## 著者と論文の取得

1. `scraping_papers.py` を実行して `papers.json` を作成
1. `create_authors.py` を実行して `_authors.xxxxyyzz.json` を作成
1. `merge_authors.py` を実行して `authors.json` を更新
1. `download.bash` を実行して論文PDFファイルを取得

```
python3 scraping_papers.py

python3 create_authors.py

python3 merge_authors.py

download.bash
```

## アップローダの使い方

環境変数でAuthorサービスとPaperサービスのエンドポイントをセットする．

```
export AUTHOR_ENDPOINT="http://192.168.201.80:32004"
export PAPER_ENDPOINT="http://192.168.201.80:30948"
```

サービスのエンドポイントは kubectl コマンドで取得する．

```
kubectl get svc -n author
kubectl get svc -n paper
```

スクリプトを実行する．

```
python upload.py
```
