import base64
import gzip
import json
from typing import Optional

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client.api_client import ApiClient

from infra_agent.models.generic import PromptToolError, SuccessPromptSummary
from infra_agent.models.k8s import (
    HelmReleaseMetadata,
    KubernetesAnyList,
    KubernetesNodeList,
    KubernetesPodLogs,
    Pod,
    PodList,
)

# Label prefixes to filter out from node labels
EXCLUDED_LABEL_PREFIXES = [
    "feature.node.kubernetes.io/",
    "node.kubernetes.io/",
    "beta.kubernetes.io/",
    "kubernetes.io/",
    "k8s.io/",
    "node-role.kubernetes.io/",
]

try:
    config.load_kube_config()
except Exception as kube_exc:
    try:
        config.load_incluster_config()
    except Exception as incluster_exc:
        raise RuntimeError(f"Failed to load Kubernetes config: kube={kube_exc}, incluster={incluster_exc}")


async def _filter_node_labels(labels: dict[str, str] | None) -> dict[str, str]:
    """Filter out system labels based on predefined prefixes."""
    if not labels:
        return {}

    result = {}
    for k, v in labels.items():
        if any(k.startswith(prefix) for prefix in EXCLUDED_LABEL_PREFIXES):
            continue
        result[k] = v
    return result


async def _validate_namespace(namespace: str) -> bool:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = await v1.list_namespace()
        return namespace in [item.metadata.name for item in ret.items]


async def list_namespaces() -> KubernetesAnyList:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = None
        try:
            ret = await v1.list_namespace()
        except Exception:
            raise PromptToolError(
                message="Failed to list namespaces",
                tool_name="list_namespaces_error",
                inputs={},
            )
        return KubernetesAnyList(items=[item.metadata.name for item in ret.items])


async def list_nodes() -> KubernetesNodeList:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = None
        try:
            ret = await v1.list_node()
        except Exception:
            raise PromptToolError(
                message="Failed to list nodes",
                tool_name="list_nodes",
                inputs={},
            )

        # Convert to dict and modify labels before validation
        data = ret.to_dict()
        for item in data.get("items", []):
            if "metadata" in item and "labels" in item["metadata"]:
                item["metadata"]["labels"] = await _filter_node_labels(item["metadata"]["labels"])

        return KubernetesNodeList.model_validate(data)


async def list_pod_containers(namespace: str, pod_name: str) -> KubernetesAnyList:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = None
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace",
                    tool_name="list_pod_containers",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            ret = await v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception:
            raise PromptToolError(
                message="Failed to list containers in pod",
                tool_name="list_pod_containers",
                inputs={
                    "namespace": namespace,
                    "pod_name": pod_name,
                },
            )
        pod = Pod.model_validate(ret.to_dict())
        return KubernetesAnyList(items=[c.name for c in pod.spec.containers])


async def get_pod_logs(
    namespace: str, pod_name: str, container_name: Optional[str] = None, tail_lines: int = 10
) -> KubernetesPodLogs:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = None
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace",
                    tool_name="get_pod_logs",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                        "container_name": container_name,
                    },
                )
            ret = await v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail_lines,
            )
        except Exception:
            raise PromptToolError(
                message="Failed to get pod logs",
                tool_name="get_pod_logs",
                inputs={
                    "namespace": namespace,
                    "pod_name": pod_name,
                    "container_name": container_name,
                },
            )
        return KubernetesPodLogs(
            container_name=container_name,
            pod_name=pod_name,
            namespace=namespace,
            logs=ret.split("\n"),
        )


async def list_pods_by_namespace(namespace: str) -> KubernetesAnyList:
    if not await _validate_namespace(namespace):
        raise PromptToolError(
            message="No such namespace", tool_name="list_pods_by_namespace", inputs={"namespace": namespace}
        )

    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        ret = None
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace", tool_name="list_pods_by_namespace", inputs={"namespace": namespace}
                )
            ret = await v1.list_namespaced_pod(namespace=namespace)
        except Exception:
            raise PromptToolError(
                message="Failed to list pods", tool_name="list_pods_by_namespace", inputs={"namespace": namespace}
            )
        data = ret.to_dict()
        pod_list = PodList.model_validate(data)
        return PodList(items=[pod.metadata.name for pod in pod_list.items])


async def delete_pod(namespace: str, pod_name: str) -> SuccessPromptSummary:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace",
                    tool_name="delete_pod",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            await v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception:
            raise PromptToolError(
                message="Failed to delete pod",
                tool_name="delete_pod",
                inputs={
                    "namespace": namespace,
                    "pod_name": pod_name,
                },
            )
        return SuccessPromptSummary()


async def get_pod_details(namespace: str, pod_name: str) -> Pod:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        pod = None
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace",
                    tool_name="get_pod_details",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            pod = await v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception:
            raise PromptToolError(
                message="No such pod",
                tool_name="get_pod_details",
                inputs={
                    "namespace": namespace,
                    "pod_name": pod_name,
                },
            )
        return Pod.model_validate(pod.to_dict())


async def list_node_pods(node_name: str) -> KubernetesAnyList:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        pods = None
        try:
            pods = await v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        except Exception:
            raise PromptToolError(
                message="Failed to list node pods", tool_name="list_node_pods", inputs={"node_name": node_name}
            )
        return PodList(items=[pod.metadata.name for pod in pods.items])


async def get_node_resources(node_name: str) -> dict:
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        node, node_metrics = None, None
        try:
            node = await v1.read_node(name=node_name)
            metrics_api = client.CustomObjectsApi(api)
            node_metrics = await metrics_api.get_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes", node_name)
        except Exception:
            raise PromptToolError(
                message="Failed to get node resources", tool_name="get_node_resources", inputs={"node_name": node_name}
            )

        capacity = node.status.capacity
        allocatable = node.status.allocatable
        usage = node_metrics.get("usage", {}) if node_metrics else {}

        return {
            "name": node_name,
            "capacity": {
                "cpu": capacity.get("cpu", "0"),
                "memory": capacity.get("memory", "0"),
                "pods": capacity.get("pods", "0"),
                "ephemeral-storage": capacity.get("ephemeral-storage", "0"),
            },
            "allocatable": {
                "cpu": allocatable.get("cpu", "0"),
                "memory": allocatable.get("memory", "0"),
                "pods": allocatable.get("pods", "0"),
                "ephemeral-storage": allocatable.get("ephemeral-storage", "0"),
            },
            "usage": {"cpu": usage.get("cpu", "0"), "memory": usage.get("memory", "0")} if usage else {},
        }


async def get_pod_helm_release_metadata(namespace: str, pod_name: str) -> dict:
    """
    Use only Kubernetes API to load the latest Helm release metadata for a given namespace and pod.
    Returns decoded metadata dict or error. Now also returns values.yaml if possible.
    """
    async with ApiClient() as api:
        v1 = client.CoreV1Api(api)
        try:
            if not await _validate_namespace(namespace):
                raise PromptToolError(
                    message="No such namespace",
                    tool_name="get_latest_helm_release_metadata",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            secrets = await v1.list_namespaced_secret(namespace=namespace)
            helm_secrets = [s for s in secrets.items if s.metadata.name.startswith("sh.helm.release.v1.")]
            if not helm_secrets:
                raise PromptToolError(
                    message="Can't find Helm release for given container",
                    tool_name="get_latest_helm_release_metadata",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            # Find the latest secret by creationTimestamp
            latest_secret = max(helm_secrets, key=lambda s: s.metadata.creation_timestamp or "")
            # The release data is in the 'data' field, key 'release'
            release_double_b64 = latest_secret.data.get("release") if latest_secret.data else None
            if not release_double_b64:
                raise PromptToolError(
                    message="No release data found in latest Helm secret",
                    tool_name="get_latest_helm_release_metadata",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
            release_b64 = base64.b64decode(release_double_b64)
            release_bytes = base64.b64decode(release_b64)
            # Helm stores a gzipped protobuf
            try:
                decompressed = gzip.decompress(release_bytes)
            except Exception:
                raise PromptToolError(
                    message="Couldn't parse Helm release metadata",
                    tool_name="get_latest_helm_release_metadata",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )

            release_str = decompressed.decode("utf-8", errors="ignore")
            if "chart" in release_str:
                start = release_str.find("{")
                end = release_str.rfind("}") + 1
                metadata_json = release_str[start:end]
                try:
                    metadata = json.loads(metadata_json)
                    return HelmReleaseMetadata(
                        name=metadata["name"],
                        namespace=namespace,
                        chart_name=metadata["chart"]["metadata"]["name"],
                        default_values=metadata["chart"]["values"],
                        current_values=metadata["config"],
                    )
                except Exception:
                    raise PromptToolError(
                        message="Couldn't parse Helm release metadata",
                        tool_name="get_latest_helm_release_metadata",
                        inputs={
                            "namespace": namespace,
                            "pod_name": pod_name,
                        },
                    )
            else:
                raise PromptToolError(
                    message="Couldn't parse Helm release metadata",
                    tool_name="get_latest_helm_release_metadata",
                    inputs={
                        "namespace": namespace,
                        "pod_name": pod_name,
                    },
                )
        except Exception:
            raise PromptToolError(
                message="Failed to decode pod's helm release metadata",
                tool_name="get_latest_helm_release_metadata",
                inputs={
                    "namespace": namespace,
                    "pod_name": pod_name,
                },
            )


# if __name__ == "__main__":
#     import asyncio
#     async def main():
#         data = await get_pod_helm_release_metadata('media', 'unmanic-5876f5c58d-g7t5v')
#         print(data)
#     asyncio.run(main())
