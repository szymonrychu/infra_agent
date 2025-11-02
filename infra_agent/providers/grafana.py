import time

import aiohttp

from infra_agent.models.generic import PromptToolError
from infra_agent.models.grafana import (
    Alert,
    GrafanaAlertList,
    GrafanaDatasource,
    GrafanaPrometheusQueryOutput,
)
from infra_agent.settings import settings

__grafana_api_headers = {
    "Authorization": f"Bearer {settings.GRAFANA_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


async def __get_datasource_id() -> int | None:
    url = f"{settings.GRAFANA_URL}api/datasources"

    datasources = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=__grafana_api_headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Query failed: {resp.status} {text}")
            datasources = [GrafanaDatasource(**d) for d in await resp.json()]

    for datasource in datasources:
        if (
            datasource.uid == settings.GRAFANA_PROMETHEUS_DATASOURCE_NAME
            and datasource.orgId == settings.GRAFANA_ORG_ID
        ):
            return datasource.id
    return None


async def __query_prometheus_range(promql: str, from_s: int, to_s: int, steps: int) -> GrafanaPrometheusQueryOutput:
    datasource_id = await __get_datasource_id()

    url = (
        f"{settings.GRAFANA_URL}api/datasources/proxy/{datasource_id}/api/v1/query_range"
        f"?query={promql}&start={from_s}&end={to_s}&step={steps}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=__grafana_api_headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Query failed: {resp.status} {text}")
            d = await resp.json()
            return GrafanaPrometheusQueryOutput.model_validate(d)


async def get_pod_container_cpu_usage(
    pod_name: str,
    namespace: str,
    container_name: str,
    from_s: int | None = None,
    to_s: int | None = None,
    steps: int | None = None,
) -> GrafanaPrometheusQueryOutput:
    if not to_s:
        to_s = round(time.time())
    if not from_s or from_s == 0:
        from_s = to_s - 60 * 60
    if not steps:
        steps = round((to_s - from_s) / 60)
    rate = round(float(to_s - from_s) / steps)
    promql = f'max(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", pod="{pod_name}", container="{container_name}"}}[{rate}s])) by (pod)'
    try:
        return await __query_prometheus_range(promql, from_s, to_s, steps)
    except Exception:
        raise PromptToolError(
            message="Failed to query Prometheus for pod container CPU usage",
            tool_name="get_pod_container_cpu_usage",
            inputs={
                "pod_name": pod_name,
                "namespace": namespace,
                "container_name": container_name,
                "from_s": from_s,
                "to_s": to_s,
                "steps": steps,
            },
        )


async def get_pod_container_memory_usage(
    pod_name: str,
    namespace: str,
    container_name: str,
    from_s: int | None = None,
    to_s: int | None = None,
    steps: int | None = None,
) -> GrafanaPrometheusQueryOutput:
    if not to_s:
        to_s = round(time.time())
    if not from_s or from_s == 0:
        from_s = to_s - 60 * 60
    if not steps:
        steps = round((to_s - from_s) / 60)
    promql = f'max(container_memory_usage_bytes{{namespace="{namespace}", pod="{pod_name}", container="{container_name}"}}) by (pod)'
    try:
        return await __query_prometheus_range(promql, from_s, to_s, steps)
    except Exception:
        raise PromptToolError(
            message="Failed to query Prometheus for pod container memory usage",
            tool_name="get_pod_container_memory_usage",
            inputs={
                "pod_name": pod_name,
                "namespace": namespace,
                "container_name": container_name,
                "from_s": from_s,
                "to_s": to_s,
                "steps": steps,
            },
        )


async def get_node_cpu_usage(
    node_name: str, from_s: int | None = None, to_s: int | None = None, steps: int | None = None
) -> GrafanaPrometheusQueryOutput:
    if not to_s:
        to_s = round(time.time())
    if not from_s or from_s == 0:
        from_s = to_s - 60 * 60
    if not steps:
        steps = round((to_s - from_s) / 60)
    rate = round(float(to_s - from_s) / steps)
    promql = f'((1 - sum without (mode) (rate(node_cpu_seconds_total{{job="node-exporter", mode=~"idle|iowait|steal", instance="{node_name}"}}[{rate}s])))/ignoring(cpu) group_left count without (cpu, mode) (node_cpu_seconds_total{{job="node-exporter", mode="idle", instance="{node_name}"}}))'
    try:
        return await __query_prometheus_range(promql, from_s, to_s, steps)
    except Exception:
        raise PromptToolError(
            message="Failed to query Prometheus for pod container CPU usage",
            tool_name="get_node_cpu_usage",
            inputs={
                "node_name": node_name,
                "from_s": from_s,
                "to_s": to_s,
                "steps": steps,
            },
        )


async def get_node_memory_usage(
    node_name: str, from_s: int | None = None, to_s: int | None = None, steps: int | None = None
) -> GrafanaPrometheusQueryOutput:
    if not to_s:
        to_s = round(time.time())
    if not from_s or from_s == 0:
        from_s = to_s - 60 * 60
    if not steps:
        steps = round((to_s - from_s) / 60)
    promql = f'(node_memory_MemTotal_bytes{{job="node-exporter", instance="{node_name}"}}-node_memory_MemFree_bytes{{job="node-exporter", instance="{node_name}"}}-node_memory_Buffers_bytes{{job="node-exporter", instance="{node_name}"}}-node_memory_Cached_bytes{{job="node-exporter", instance="{node_name}"}})'
    try:
        return await __query_prometheus_range(promql, from_s, to_s, steps)
    except Exception:
        raise PromptToolError(
            message="Failed to query Prometheus for pod container CPU usage",
            tool_name="get_node_memory_usage",
            inputs={
                "node_name": node_name,
                "from_s": from_s,
                "to_s": to_s,
                "steps": steps,
            },
        )


async def list_grafana_alerts() -> GrafanaAlertList:
    """List alerts from Grafana API."""
    url = f"{settings.GRAFANA_URL}api/alerts"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=__grafana_api_headers) as resp:
            await resp.text()
            if resp.status != 200:
                raise PromptToolError(
                    message="Failed to query Prometheus for pod container CPU usage",
                    tool_name="get_node_memory_usage",
                    inputs={},
                )
            alerts_data = await resp.json()
            alerts = [Alert(**a) for a in alerts_data]
            return GrafanaAlertList(alerts=alerts)


# async def main():
#     to_s = round(time.time())
#     from_s = round(to_s - 60 * 60)
#     steps = 60
#     data = await get_pod_container_memory_usage('jellyfin', 'media', 'jellyfin', from_s, to_s, steps)
#     print(data)

# if __name__ == "__main__":
#     asyncio.run(main())

# curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
#     -H "Accept: application/json" \
#     https://grafana.szymonrichert.pl/api/datasources | jq
