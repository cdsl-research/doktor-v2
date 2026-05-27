# deploy

doktor-v2 のKubernetesマニフェストとデプロイ手順。

## 認証情報（Secret）について

DB類（MongoDB / mongo-express / MinIO）の認証情報はマニフェストに平文で持たず、
Kubernetes Secret を参照する。Secret はリポジトリにコミットせず、デプロイ時に
`kubectl create secret` で各名前空間に作成する。

各Deploymentが参照するSecretは以下のとおり。

| 名前空間 | Secret名 | キー | 利用先 |
|---|---|---|---|
| paper | `paper-mongo-secret` | `username`, `password` | paper-mongo / paper-mongo-express |
| paper | `paper-minio-secret` | `accesskey`, `secretkey` | paper-minio |
| author | `author-mongo-secret` | `username`, `password` | author-mongo / author-mongo-express |
| stats | `stats-mongo-secret` | `username`, `password` | stats-mongo / stats-mongo-express |
| thumbnail | `thumbnail-minio-secret` | `accesskey`, `secretkey` | thumbnail-minio |

## デプロイ手順

### 1. 名前空間の作成

```bash
kubectl apply -f author/author-ns.yml
kubectl apply -f paper/paper-ns.yml
kubectl apply -f stats/stats-ns.yml
kubectl apply -f thumbnail/thumbnail-ns.yml
kubectl apply -f front/front-ns.yml
kubectl apply -f front-admin/front-admin-ns.yml
kubectl apply -f fulltext/fulltext-ns.yml
```

### 2. Secretの作成

**Deploymentを適用する前に**作成すること。未作成だとPodが `CreateContainerConfigError` で起動しない。
下記の値は現行のデフォルト値。本番運用では適宜変更すること。

```bash
# paper
kubectl create secret generic paper-mongo-secret -n paper \
  --from-literal=username=root --from-literal=password=example
kubectl create secret generic paper-minio-secret -n paper \
  --from-literal=accesskey=minio --from-literal=secretkey=minio123

# author
kubectl create secret generic author-mongo-secret -n author \
  --from-literal=username=root --from-literal=password=example

# stats
kubectl create secret generic stats-mongo-secret -n stats \
  --from-literal=username=root --from-literal=password=example

# thumbnail
kubectl create secret generic thumbnail-minio-secret -n thumbnail \
  --from-literal=accesskey=minio --from-literal=secretkey=minio123
```

### 3. マニフェストの適用

```bash
kubectl apply -f author/
kubectl apply -f paper/
kubectl apply -f stats/
kubectl apply -f thumbnail/
kubectl apply -f fulltext/
kubectl apply -f front/
kubectl apply -f front-admin/
```

## Secretの値を更新する

値を変更する場合は、Secretを作り直してから対象のPodを再起動する
（Secret更新は稼働中のPodの環境変数に自動反映されないため）。

```bash
# 例: paper-mongo-secret のパスワードを変更
kubectl create secret generic paper-mongo-secret -n paper \
  --from-literal=username=root --from-literal=password=<new-password> \
  --dry-run=client -o yaml | kubectl apply -f -

# 参照しているDeploymentを再起動
kubectl rollout restart deployment/paper-mongo-deploy -n paper
kubectl rollout restart deployment/paper-mongo-express-deploy -n paper
```

> 注意: MongoDBの `MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD` は
> **データ初期化時にのみ有効**。既存のPVCがある状態で値を変えても既存DBの資格情報は
> 変わらない。資格情報を変える場合はDB側でユーザを更新するか、PVCを作り直す必要がある。
