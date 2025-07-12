import glob
import os
from collections import defaultdict
from pathlib import Path

import yaml

OUTPUT_DIR = Path(__file__).parent.resolve()
# YAMLファイルのパスをpathlibで取得
yaml_dir = OUTPUT_DIR.parent / "deploy"
yaml_files = list(yaml_dir.glob("*/*.yml"))

resources = {}  # 各リソース情報を格納

for f in yaml_files:
    with open(f, "r") as file:
        try:
            docs = list(yaml.safe_load_all(file))
            for doc in docs:
                if not doc:
                    continue
                kind = doc.get("kind")
                name = doc.get("metadata", {}).get("name")
                # Namespaceの抽出（なければ'default'）
                namespace = doc.get("metadata", {}).get("namespace")
                if not namespace:
                    # Namespaceリソース自身はnameをnamespaceとみなす
                    if kind == "Namespace":
                        namespace = name
                    else:
                        namespace = "default"
                labels = doc.get("metadata", {}).get("labels", {})
                # if kind: Deployment
                env_vars = []
                if kind == "Deployment":
                    # get env vars
                    containers = (
                        doc.get("spec", {})
                        .get("template", {})
                        .get("spec", {})
                        .get("containers", [])
                    )
                    for container in containers:
                        envs = container.get("env", [])
                        for env in envs:
                            # get env value and set to env_var_index
                            value = env.get("value", "")
                            if value:
                                env_vars.append(value)
                                print(f"env_vars: {env_vars}")
                resources[(kind, name, namespace)] = {
                    "file": str(f),
                    "kind": kind,
                    "name": name,
                    "namespace": namespace,
                    "labels": labels,
                    "doc": doc,
                    "env_vars": env_vars,
                }
                # name_kind_map[(kind, name, namespace)] = doc

        except Exception as e:
            print(f"Error parsing {f}: {e}")

# 依存関係の集計
deps = defaultdict(
    list
)  # key: (kind, name, namespace), value: list of (kind, name, namespace)


def extract_pvc_from_volumes(volumes):
    pvc_names = []
    if not volumes:
        return pvc_names
    for v in volumes:
        claim = v.get("persistentVolumeClaim")
        if claim and "claimName" in claim:
            pvc_names.append(claim["claimName"])
    return pvc_names


# PVCとDeploymentの依存関係を追加
for k, spec in resources.items():
    kind = spec["kind"]
    name = spec["name"]
    namespace = spec["namespace"]
    doc = spec["doc"]

    # Deployment, StatefulSet, Pod => PVCをさがす
    if kind in ["Deployment", "StatefulSet", "Pod"]:
        tpl = doc.get("spec", {}).get("template", {})
        spec2 = tpl.get("spec", {}) if tpl else doc.get("spec", {})
        volumes = spec2.get("volumes", [])
        pvc_names = extract_pvc_from_volumes(volumes)
        for pvc in pvc_names:
            # PVCは同じnamespaceにある前提
            deps[(kind, name, namespace)].append(
                ("PersistentVolumeClaim", pvc, namespace)
            )

    # Service => Deployment
    if kind == "Service":
        selector = doc.get("spec", {}).get("selector", {})
        for dep in resources.values():
            if dep["kind"] == "Deployment":
                if selector and all(
                    item in dep["labels"].items() for item in selector.items()
                ):
                    deps[("Service", name, namespace)].append(
                        ("Deployment", dep["name"], dep["namespace"])
                    )

    # Deployment => Service
    if kind in ["Deployment", "StatefulSet", "Pod"]:
        env_vars = spec.get("env_vars")
        if env_vars is None:
            continue
        for env_var in env_vars:
            # 環境変数の中にドメイン名が含まれているかを探す
            for k, spec in resources.items():
                if spec["kind"] == "Service":
                    domain_name = spec["name"] + "." + spec["namespace"]
                    print(
                        f"compare: {domain_name} in {env_var}:", domain_name in env_var
                    )
                    if domain_name in env_var:
                        deps[("Deployment", name, namespace)].append(k)

# 結果表示
print("\n--- 依存関係 ---")
for k, v in deps.items():
    print(f"{k} depends on {v}")


# Graphviz dot形式で出力
def to_dot(deps):
    lines = ["digraph G {"]
    for src, targets in deps.items():
        src_label = f"{src[0]}:{src[1]}\\n[{src[2]}]"
        for tgt in targets:
            tgt_label = f"{tgt[0]}:{tgt[1]}\\n[{tgt[2]}]"
            lines.append(f'    "{src_label}" -> "{tgt_label}";')
    lines.append("}")
    return "\n".join(lines)


dot_path = OUTPUT_DIR / "dependency_graph.dot"
dot_str = to_dot(deps)
with open(dot_path, "w") as f:
    f.write(dot_str)
print(f"\nGraphviz dotファイルを書き出しました: {dot_path.relative_to(Path.cwd())}")
