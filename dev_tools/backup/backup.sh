#!/usr/bin/env bash
#
# doktor-v2 の MongoDB / Elasticsearch / MinIO をVMからkubectl port-forward経由でバックアップする。
#
# 前提となる外部コマンド: kubectl, mongodump, elasticdump, mc, base64, gzip, grep
# (インストール方法は README.md を参照。Bash 4以上が必要)

set -uo pipefail

PORT_FORWARD_READY_TIMEOUT=30

# namespace:service:port:db_name:secret_name
MONGO_TARGETS=(
  "paper:paper-mongo:27017:paper:paper-mongo-secret"
  "author:author-mongo:27017:author:author-mongo-secret"
  "stats:stats-mongo:27017:stats:stats-mongo-secret"
)

# namespace:service:port:index_name
ES_TARGETS=(
  "fulltext:fulltext-elastic:9200:fulltext"
)

# namespace:service:port:bucket_name:secret_name
MINIO_TARGETS=(
  "paper:paper-minio:9000:paper:paper-minio-secret"
  "thumbnail:thumbnail-minio:9000:thumbnail:thumbnail-minio-secret"
)

OUTPUT_DIR="./backups"
TYPES="mongo,elasticsearch,minio"
DRY_RUN=0

PF_PID=""
PF_LOGFILE=""

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$*"
}

usage() {
  cat <<'EOF'
使い方: backup.sh [--output-dir DIR] [--types mongo,elasticsearch,minio] [--dry-run]

オプション:
  --output-dir DIR  バックアップの出力先ディレクトリ (デフォルト: ./backups)
  --types LIST      バックアップ対象の種別をカンマ区切りで指定 (mongo,elasticsearch,minio)
  --dry-run         実際にはコマンドを実行せず、実行予定の内容のみ表示する
  -h, --help        このヘルプを表示する
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --output-dir)
        OUTPUT_DIR="$2"
        shift 2
        ;;
      --types)
        TYPES="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "不明なオプションです: $1" >&2
        usage >&2
        exit 2
        ;;
    esac
  done
}

validate_types() {
  local t
  for t in "${TYPE_LIST[@]}"; do
    case "$t" in
      mongo|elasticsearch|minio) ;;
      *)
        echo "不明な種別です: $t (選択可能: mongo, elasticsearch, minio)" >&2
        exit 2
        ;;
    esac
  done
}

check_tools() {
  local -A needed=()
  local t
  for t in "${TYPE_LIST[@]}"; do
    case "$t" in
      mongo) needed[kubectl]=1; needed[mongodump]=1 ;;
      elasticsearch) needed[kubectl]=1; needed[elasticdump]=1 ;;
      minio) needed[kubectl]=1; needed[mc]=1 ;;
    esac
  done
  local missing=()
  local tool
  for tool in "${!needed[@]}"; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    IFS=$'\n' missing=($(sort <<<"${missing[*]}")); unset IFS
    local joined
    joined=$(printf '%s, ' "${missing[@]}")
    joined="${joined%, }"
    echo "エラー: 次のコマンドが見つかりません。インストールしてから再実行してください: $joined" >&2
    exit 1
  fi
}

# get_secret <namespace> <secret_name> <key>
get_secret() {
  local ns="$1" secret="$2" key="$3"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] kubectl get secret -n $ns $secret -o jsonpath={.data.$key}"
    echo "DRY-RUN-VALUE"
    return 0
  fi
  local encoded
  if ! encoded=$(kubectl get secret -n "$ns" "$secret" -o "jsonpath={.data.$key}" 2>&1); then
    echo "Secret取得に失敗: namespace=$ns secret=$secret key=$key: $encoded" >&2
    return 1
  fi
  if [[ -z "$encoded" ]]; then
    echo "Secret取得に失敗(空): namespace=$ns secret=$secret key=$key" >&2
    return 1
  fi
  base64 -d <<< "$encoded"
}

# start_port_forward <namespace> <service> <port>
start_port_forward() {
  local ns="$1" svc="$2" port="$3"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] kubectl port-forward -n $ns svc/$svc $port:$port"
    return 0
  fi
  log "port-forward開始: kubectl port-forward -n $ns svc/$svc $port:$port"
  PF_LOGFILE="$(mktemp)"
  kubectl port-forward -n "$ns" "svc/$svc" "$port:$port" >"$PF_LOGFILE" 2>&1 &
  PF_PID=$!
  local waited=0
  while [[ "$waited" -lt "$PORT_FORWARD_READY_TIMEOUT" ]]; do
    if ! kill -0 "$PF_PID" 2>/dev/null; then
      cat "$PF_LOGFILE" >&2
      echo "kubectl port-forward が異常終了しました (namespace=$ns service=$svc)" >&2
      stop_port_forward
      return 1
    fi
    if grep -q "Forwarding from" "$PF_LOGFILE" 2>/dev/null; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  echo "port-forwardの準備がタイムアウトしました (namespace=$ns service=$svc)" >&2
  stop_port_forward
  return 1
}

stop_port_forward() {
  if [[ -n "$PF_PID" ]]; then
    kill "$PF_PID" 2>/dev/null || true
    wait "$PF_PID" 2>/dev/null || true
    PF_PID=""
  fi
  if [[ -n "$PF_LOGFILE" ]]; then
    rm -f "$PF_LOGFILE"
    PF_LOGFILE=""
  fi
}

cleanup_on_exit() {
  stop_port_forward
}
trap cleanup_on_exit EXIT INT TERM

# run_cmd <display string> <argv...>
run_cmd() {
  local display="$1"
  shift
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] $display"
    return 0
  fi
  log "実行: $display"
  if ! "$@"; then
    local rc=$?
    echo "コマンドが失敗しました (exit=$rc): $display" >&2
    return "$rc"
  fi
}

# backup_mongo <entry> <out_dir>
backup_mongo() {
  local entry="$1" out_dir="$2"
  local ns svc port db secret
  IFS=':' read -r ns svc port db secret <<< "$entry"

  local user pass
  user=$(get_secret "$ns" "$secret" username) || return 1
  pass=$(get_secret "$ns" "$secret" password) || return 1

  start_port_forward "$ns" "$svc" "$port" || return 1

  local dest="$out_dir/mongo/$svc"
  local display="mongodump --host=localhost --port=$port --username=*** --password=*** --authenticationDatabase=admin --db=$db --gzip --out=$dest"
  run_cmd "$display" mongodump \
    "--host=localhost" "--port=$port" \
    "--username=$user" "--password=$pass" \
    "--authenticationDatabase=admin" "--db=$db" \
    "--gzip" "--out=$dest"
  local rc=$?
  stop_port_forward
  return "$rc"
}

# backup_elasticsearch <entry> <out_dir>
backup_elasticsearch() {
  local entry="$1" out_dir="$2"
  local ns svc port index
  IFS=':' read -r ns svc port index <<< "$entry"

  start_port_forward "$ns" "$svc" "$port" || return 1

  local input_url="http://localhost:$port/$index"
  local dest_dir="$out_dir/elasticsearch/$index"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$dest_dir"
  fi

  local rc=0
  local dtype fname dest display
  for pair in "mapping:mapping.json.gz" "data:data.json.gz"; do
    IFS=':' read -r dtype fname <<< "$pair"
    dest="$dest_dir/$fname"
    display="elasticdump --input=$input_url --output=\$ --type=$dtype | gzip > $dest"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      log "[dry-run] $display"
      continue
    fi
    log "実行: $display"
    if ! elasticdump "--input=$input_url" '--output=$' "--type=$dtype" | gzip > "$dest"; then
      echo "コマンドが失敗しました: $display" >&2
      rc=1
    fi
  done

  stop_port_forward
  return "$rc"
}

# backup_minio <entry> <out_dir>
backup_minio() {
  local entry="$1" out_dir="$2"
  local ns svc port bucket secret
  IFS=':' read -r ns svc port bucket secret <<< "$entry"

  local accesskey secretkey
  accesskey=$(get_secret "$ns" "$secret" accesskey) || return 1
  secretkey=$(get_secret "$ns" "$secret" secretkey) || return 1

  start_port_forward "$ns" "$svc" "$port" || return 1

  local alias="doktor-backup-$svc"
  local rc=0

  run_cmd "mc alias set $alias http://localhost:$port *** ***" \
    mc alias set "$alias" "http://localhost:$port" "$accesskey" "$secretkey" || rc=1

  if [[ "$rc" -eq 0 ]]; then
    local dest="$out_dir/minio/$bucket"
    run_cmd "mc mirror --overwrite $alias/$bucket $dest" \
      mc mirror --overwrite "$alias/$bucket" "$dest" || rc=1
  fi

  run_cmd "mc alias remove $alias" mc alias remove "$alias" || true

  stop_port_forward
  return "$rc"
}

main() {
  parse_args "$@"

  IFS=',' read -ra TYPE_LIST <<< "$TYPES"
  validate_types

  if [[ "$DRY_RUN" -eq 0 ]]; then
    check_tools
  fi

  local timestamp out_dir
  timestamp="$(date '+%Y%m%d_%H%M%S')"
  out_dir="$OUTPUT_DIR/$timestamp"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$out_dir"
  fi
  log "バックアップ出力先: $out_dir"

  local job_names=() job_ok=()
  local type entry

  for type in "${TYPE_LIST[@]}"; do
    case "$type" in
      mongo)
        for entry in "${MONGO_TARGETS[@]}"; do
          local svc="${entry#*:}"; svc="${svc%%:*}"
          local name="mongo/$svc"
          log "=== $name のバックアップを開始 ==="
          if backup_mongo "$entry" "$out_dir"; then
            job_names+=("$name"); job_ok+=(1)
            log "=== $name のバックアップが完了 ==="
          else
            job_names+=("$name"); job_ok+=(0)
            log "=== $name のバックアップに失敗 ==="
          fi
        done
        ;;
      elasticsearch)
        for entry in "${ES_TARGETS[@]}"; do
          local index="${entry##*:}"
          local name="elasticsearch/$index"
          log "=== $name のバックアップを開始 ==="
          if backup_elasticsearch "$entry" "$out_dir"; then
            job_names+=("$name"); job_ok+=(1)
            log "=== $name のバックアップが完了 ==="
          else
            job_names+=("$name"); job_ok+=(0)
            log "=== $name のバックアップに失敗 ==="
          fi
        done
        ;;
      minio)
        for entry in "${MINIO_TARGETS[@]}"; do
          local bucket="${entry%:*}"; bucket="${bucket##*:}"
          local name="minio/$bucket"
          log "=== $name のバックアップを開始 ==="
          if backup_minio "$entry" "$out_dir"; then
            job_names+=("$name"); job_ok+=(1)
            log "=== $name のバックアップが完了 ==="
          else
            job_names+=("$name"); job_ok+=(0)
            log "=== $name のバックアップに失敗 ==="
          fi
        done
        ;;
    esac
  done

  log "--- 結果サマリ ---"
  local i failed=0
  for i in "${!job_names[@]}"; do
    if [[ "${job_ok[$i]}" -eq 1 ]]; then
      log "  OK: ${job_names[$i]}"
    else
      log "  FAILED: ${job_names[$i]}"
      failed=1
    fi
  done

  exit "$failed"
}

main "$@"
