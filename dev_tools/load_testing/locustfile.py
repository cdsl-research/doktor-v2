"""
doktor.tak-cslab.org 負荷テスト用 Locust シナリオ

使用方法:
    locust -f locustfile.py --host=https://doktor.tak-cslab.org
"""

import random
from pathlib import Path

from locust import HttpUser, between, task


def load_paper_ids(filename: str = "paper_ids.txt") -> list[str]:
    """論文IDリストをファイルから読み込む"""
    path = Path(__file__).parent / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{filename} が見つかりません。ログ解析スクリプトを先に実行してください。"
        )
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


# 論文IDをモジュール読み込み時にロード
PAPER_IDS = load_paper_ids()

# ログ解析結果に基づくダウンロード確率（論文詳細閲覧後にダウンロードする確率）
DOWNLOAD_PROBABILITY = 0.47


class DoktorUser(HttpUser):
    """典型的なユーザーの行動パターンをシミュレート"""

    wait_time = between(1, 5)

    @task(3)
    def browse_paper_flow(self):
        """トップページ → 論文詳細 → (確率的に)ダウンロード のフロー"""
        # 1. トップページを閲覧
        self.client.get("/", name="トップページ")

        # 2. 論文詳細ページを閲覧
        paper_id = random.choice(PAPER_IDS)
        self.client.get(f"/paper/{paper_id}", name="論文詳細")

        # 3. 一定確率でダウンロード
        if random.random() < DOWNLOAD_PROBABILITY:
            self.client.get(f"/paper/{paper_id}/download", name="論文ダウンロード")

    @task(1)
    def direct_paper_access(self):
        """検索エンジン等から直接論文ページにアクセスするパターン"""
        paper_id = random.choice(PAPER_IDS)
        self.client.get(f"/paper/{paper_id}", name="論文詳細")

        if random.random() < DOWNLOAD_PROBABILITY:
            self.client.get(f"/paper/{paper_id}/download", name="論文ダウンロード")
