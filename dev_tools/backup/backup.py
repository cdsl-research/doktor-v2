#!/usr/bin/env python3
"""doktor-v2 の MongoDB / Elasticsearch / MinIO をVMからkubectl port-forward経由でバックアップする。

前提となる外部コマンド: kubectl, mongodump, elasticdump, mc
(インストール方法は README.md を参照)
"""
import argparse
import base64
import gzip
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REQUIRED_TOOLS = {
    "mongo": ["kubectl", "mongodump"],
    "elasticsearch": ["kubectl", "elasticdump"],
    "minio": ["kubectl", "mc"],
}

PORT_FORWARD_READY_TIMEOUT = 30


@dataclass(frozen=True)
class MongoTarget:
    namespace: str
    service: str
    port: int
    db_name: str
    secret_name: str


@dataclass(frozen=True)
class ElasticsearchTarget:
    namespace: str
    service: str
    port: int
    index_name: str


@dataclass(frozen=True)
class MinioTarget:
    namespace: str
    service: str
    port: int
    bucket_name: str
    secret_name: str


MONGO_TARGETS = [
    MongoTarget("paper", "paper-mongo", 27017, "paper", "paper-mongo-secret"),
    MongoTarget("author", "author-mongo", 27017, "author", "author-mongo-secret"),
    MongoTarget("stats", "stats-mongo", 27017, "stats", "stats-mongo-secret"),
]

ELASTICSEARCH_TARGETS = [
    ElasticsearchTarget("fulltext", "fulltext-elastic", 9200, "fulltext"),
]

MINIO_TARGETS = [
    MinioTarget("paper", "paper-minio", 9000, "paper", "paper-minio-secret"),
    MinioTarget("thumbnail", "thumbnail-minio", 9000, "thumbnail", "thumbnail-minio-secret"),
]


class BackupError(Exception):
    pass


def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def check_tools(types: list[str]) -> None:
    missing = []
    needed = set()
    for t in types:
        needed.update(REQUIRED_TOOLS[t])
    for tool in sorted(needed):
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        raise BackupError(
            "次のコマンドが見つかりません。インストールしてから再実行してください: "
            + ", ".join(missing)
        )


def get_secret_value(namespace: str, secret_name: str, key: str, dry_run: bool) -> str:
    cmd = [
        "kubectl", "get", "secret", "-n", namespace, secret_name,
        "-o", f"jsonpath={{.data.{key}}}",
    ]
    if dry_run:
        log(f"[dry-run] {' '.join(cmd)}")
        return "DRY-RUN-VALUE"
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise BackupError(
            f"Secret取得に失敗: namespace={namespace} secret={secret_name} key={key} "
            f"stderr={result.stderr.strip()}"
        )
    return base64.b64decode(result.stdout.strip()).decode()


class PortForward:
    """kubectl port-forward をバックグラウンドで起動し、準備完了を待ってから使う。"""

    def __init__(self, namespace: str, service: str, port: int, dry_run: bool):
        self.namespace = namespace
        self.service = service
        self.port = port
        self.dry_run = dry_run
        self.process: subprocess.Popen | None = None

    def __enter__(self) -> "PortForward":
        cmd = [
            "kubectl", "port-forward", "-n", self.namespace,
            f"svc/{self.service}", f"{self.port}:{self.port}",
        ]
        if self.dry_run:
            log(f"[dry-run] {' '.join(cmd)}")
            return self
        log(f"port-forward開始: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            self._wait_ready()
        except BackupError:
            self._terminate()
            raise
        return self

    def _wait_ready(self) -> None:
        assert self.process is not None
        deadline = time.monotonic() + PORT_FORWARD_READY_TIMEOUT
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise BackupError(
                    f"kubectl port-forward が異常終了しました "
                    f"(namespace={self.namespace} service={self.service})"
                )
            line = self.process.stdout.readline()
            if not line:
                continue
            log(f"  {line.rstrip()}")
            if "Forwarding from" in line:
                return
        raise BackupError(
            f"port-forwardの準備がタイムアウトしました "
            f"(namespace={self.namespace} service={self.service})"
        )

    def __exit__(self, exc_type, exc, tb) -> None:
        self._terminate()

    def _terminate(self) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process = None


def run_cmd(cmd: list[str], dry_run: bool) -> None:
    if dry_run:
        log(f"[dry-run] {' '.join(cmd)}")
        return
    log(f"実行: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise BackupError(f"コマンドが失敗しました (exit={result.returncode}): {' '.join(cmd)}")


def run_cmd_to_gzip(cmd: list[str], dest: Path, dry_run: bool) -> None:
    if dry_run:
        log(f"[dry-run] {' '.join(cmd)} > {dest}")
        return
    log(f"実行: {' '.join(cmd)} > {dest}")
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc, gzip.open(dest, "wb") as out:
        assert proc.stdout is not None
        shutil.copyfileobj(proc.stdout, out)
        proc.wait()
    if proc.returncode != 0:
        raise BackupError(f"コマンドが失敗しました (exit={proc.returncode}): {' '.join(cmd)}")


def backup_mongo(target: MongoTarget, out_dir: Path, dry_run: bool) -> None:
    username = get_secret_value(target.namespace, target.secret_name, "username", dry_run)
    password = get_secret_value(target.namespace, target.secret_name, "password", dry_run)
    with PortForward(target.namespace, target.service, target.port, dry_run):
        uri = (
            f"mongodb://{urllib.parse.quote_plus(username)}:"
            f"{urllib.parse.quote_plus(password)}@localhost:{target.port}/"
            f"{target.db_name}?authSource=admin"
        )
        dest = out_dir / "mongo" / target.service
        cmd = ["mongodump", f"--uri={uri}", "--gzip", f"--out={dest}"]
        run_cmd(cmd, dry_run)


def backup_elasticsearch(target: ElasticsearchTarget, out_dir: Path, dry_run: bool) -> None:
    with PortForward(target.namespace, target.service, target.port, dry_run):
        input_url = f"http://localhost:{target.port}/{target.index_name}"
        dest_dir = out_dir / "elasticsearch" / target.index_name
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
        for dump_type, filename in (("mapping", "mapping.json.gz"), ("data", "data.json.gz")):
            cmd = ["elasticdump", f"--input={input_url}", "--output=$", f"--type={dump_type}"]
            run_cmd_to_gzip(cmd, dest_dir / filename, dry_run)


def backup_minio(target: MinioTarget, out_dir: Path, dry_run: bool) -> None:
    accesskey = get_secret_value(target.namespace, target.secret_name, "accesskey", dry_run)
    secretkey = get_secret_value(target.namespace, target.secret_name, "secretkey", dry_run)
    alias = f"doktor-backup-{target.service}"
    with PortForward(target.namespace, target.service, target.port, dry_run):
        run_cmd(
            ["mc", "alias", "set", alias, f"http://localhost:{target.port}", accesskey, secretkey],
            dry_run,
        )
        try:
            dest = out_dir / "minio" / target.bucket_name
            run_cmd(
                ["mc", "mirror", "--overwrite", f"{alias}/{target.bucket_name}", str(dest)],
                dry_run,
            )
        finally:
            run_cmd(["mc", "alias", "remove", alias], dry_run)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("./backups"),
        help="バックアップの出力先ディレクトリ (デフォルト: ./backups)",
    )
    parser.add_argument(
        "--types", default="mongo,elasticsearch,minio",
        help="バックアップ対象の種別をカンマ区切りで指定 (mongo,elasticsearch,minio)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="実際にはコマンドを実行せず、実行予定の内容のみ表示する",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    for t in types:
        if t not in REQUIRED_TOOLS:
            print(f"不明な種別です: {t} (選択可能: {', '.join(REQUIRED_TOOLS)})", file=sys.stderr)
            return 2

    if not args.dry_run:
        try:
            check_tools(types)
        except BackupError as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.output_dir / timestamp
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    log(f"バックアップ出力先: {out_dir}")

    jobs: list[tuple[str, callable]] = []
    if "mongo" in types:
        for target in MONGO_TARGETS:
            jobs.append((f"mongo/{target.service}", lambda t=target: backup_mongo(t, out_dir, args.dry_run)))
    if "elasticsearch" in types:
        for target in ELASTICSEARCH_TARGETS:
            jobs.append((f"elasticsearch/{target.index_name}", lambda t=target: backup_elasticsearch(t, out_dir, args.dry_run)))
    if "minio" in types:
        for target in MINIO_TARGETS:
            jobs.append((f"minio/{target.bucket_name}", lambda t=target: backup_minio(t, out_dir, args.dry_run)))

    results: dict[str, bool] = {}
    for name, job in jobs:
        log(f"=== {name} のバックアップを開始 ===")
        try:
            job()
            results[name] = True
            log(f"=== {name} のバックアップが完了 ===")
        except BackupError as e:
            results[name] = False
            log(f"=== {name} のバックアップに失敗: {e} ===")

    log("--- 結果サマリ ---")
    failed = [name for name, ok in results.items() if not ok]
    for name, ok in results.items():
        log(f"  {'OK' if ok else 'FAILED'}: {name}")

    return 1 if failed else 0


def _install_signal_handlers() -> None:
    def handler(signum, frame):
        log(f"シグナル {signum} を受信。処理を中断します。")
        sys.exit(130)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


if __name__ == "__main__":
    _install_signal_handlers()
    sys.exit(main(sys.argv[1:]))
