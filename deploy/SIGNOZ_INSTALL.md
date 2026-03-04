以下のリンクを見ながらインストールする．

[K8s Infra - Install | SigNoz](https://signoz.io/docs/collection-agents/k8s/k8s-infra/install-k8s-infra/)

```
helm repo add signoz https://charts.signoz.io
helm repo update
```

Configの作成

https://github.com/cdsl-research/doktor-v2/blob/master/deploy/signoz-values.yml

Namespaceの作成

```
cdsl@doktor-share-ancher:~/doktor-v2/deploy$ kubectl create ns signoz
namespace/signoz created
```

インストール

```
cdsl@doktor-share-ancher:~/doktor-v2/deploy$ helm install signoz-k8s signoz/k8s-infra -f signoz-values-dev.yml -n signoz
NAME: signoz-k8s
LAST DEPLOYED: Mon Oct 13 06:33:42 2025
NAMESPACE: signoz
STATUS: deployed
REVISION: 1
NOTES:
You have just deployed k8s-infra chart:

- otel-agent version: '0.109.0'
- otel-deployment version: '0.109.0'
```

確認

```
cdsl@doktor-share-ancher:~/doktor-v2/deploy$ kubectl get svc -n signoz
NAME                                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)                                AGE
signoz-k8s-k8s-infra-otel-agent        ClusterIP   10.43.62.140   <none>        13133/TCP,8888/TCP,4317/TCP,4318/TCP   8s
signoz-k8s-k8s-infra-otel-deployment   ClusterIP   10.43.39.131   <none>        13133/TCP                              8s

cdsl@doktor-share-ancher:~/doktor-v2/deploy$ kubectl get pod -n signoz
NAME                                                    READY   STATUS    RESTARTS   AGE
signoz-k8s-k8s-infra-otel-agent-b28gl                   1/1     Running   0          38s
signoz-k8s-k8s-infra-otel-agent-jvhk8                   1/1     Running   0          38s
signoz-k8s-k8s-infra-otel-agent-qs4td                   1/1     Running   0          38s
signoz-k8s-k8s-infra-otel-agent-zmmgb                   1/1     Running   0          38s
signoz-k8s-k8s-infra-otel-deployment-7b49cdc86c-ttwj8   1/1     Running   0          38s
```

アプリケーションのOTelアドレスをgrpcで以下にセットする．

http://signoz-k8s-k8s-infra-otel-agent.signoz.svc.cluster.local:4317

OTel SDKを使っている場合には, Podの構成で以下のように設定を行う．

```yaml
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "k8s.pod.name=$(POD_NAME),k8s.namespace.name=$(POD_NAMESPACE),k8s.node.name=$(NODE_NAME)"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://signoz-k8s-k8s-infra-otel-agent.signoz.svc.cluster.local:4317"
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: "grpc"
            - name: OTEL_EXPORTER_OTLP_INSECURE
              value: "true"
            - name: OTEL_SERVICE_NAME
              value: "front"
```

更新

```
(env) koyama@doktor-share-ancher:~/doktor-v2/deploy$ helm upgrade signoz-k8s signoz/k8s-infra -f signoz-values-kube.yml -n signoz
Release "signoz-k8s" has been upgraded. Happy Helming!
NAME: signoz-k8s
LAST DEPLOYED: Wed Mar  4 01:19:41 2026
NAMESPACE: signoz
STATUS: deployed
REVISION: 2
NOTES:
You have just deployed k8s-infra chart:

- otel-agent version: '0.139.0'
- otel-deployment version: '0.139.0'
```
