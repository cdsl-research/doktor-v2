# sample-data-uploader

## Setup

1. `scraping_papers.py` を実行して `papers.json` を作成

```
python3 scraping_papers.py
```

2. `create_authors.py` を実行して `_authors.xxxxyyzz.json` を作成

```
python3 create_authors.py
```

3. `merge_authors.py` を実行して `authors.json` を更新

```
python3 merge_authors.py
```

4. `pre_upload.sh` を実行して環境変数を設定

```
. pre_upload.sh
export | grep -i endpo
```

5. gdown をインストール

```
pip install gdown
```

6. `download.bash` を実行して論文PDFファイルを取得

```
./download.bash
```

7. `upload.py` を実行して論文PDFファイルをアップロード

```
pip install requests

python3 upload.py
```
