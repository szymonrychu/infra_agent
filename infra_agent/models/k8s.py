from typing import Any, Dict, List, Optional

from pydantic import Field

from infra_agent.models.generic import InfraAgentBaseModel


class NodeAddress(InfraAgentBaseModel):
    """Represents a node address in Kubernetes"""

    type: str
    address: str


class NodeSystemInfo(InfraAgentBaseModel):
    """Information about the node's system"""

    machine_id: Optional[str] = Field(None, alias="machineID")
    system_uuid: Optional[str] = Field(None, alias="systemUUID")
    boot_id: Optional[str] = Field(None, alias="bootID")
    kernel_version: Optional[str] = Field(None, alias="kernelVersion")
    os_image: Optional[str] = Field(None, alias="osImage")
    container_runtime_version: Optional[str] = Field(None, alias="containerRuntimeVersion")
    kubelet_version: Optional[str] = Field(None, alias="kubeletVersion")
    kube_proxy_version: Optional[str] = Field(None, alias="kubeProxyVersion")
    operating_system: Optional[str] = Field(None, alias="operatingSystem")
    architecture: Optional[str] = Field(None, alias="architecture")


class NodeCondition(InfraAgentBaseModel):
    """Represents a node condition"""

    type: str
    status: str
    # last_heartbeat_time: Optional[datetime] = Field(None, alias="lastHeartbeatTime")
    # last_transition_time: Optional[datetime] = Field(None, alias="lastTransitionTime")
    reason: Optional[str] = None
    message: Optional[str] = None

    # @property
    # def heartbeat_at(self) -> Optional[datetime]:
    #     """Return heartbeat time as datetime object"""
    #     return self.last_heartbeat_time

    # @property
    # def transitioned_at(self) -> Optional[datetime]:
    #     """Return transition time as datetime object"""
    #     return self.last_transition_time


class NodeStatus(InfraAgentBaseModel):
    """Status information about the node"""

    capacity: Optional[dict[str, str]] = Field(default_factory=dict)
    allocatable: Optional[dict[str, str]] = Field(default_factory=dict)
    conditions: Optional[List[NodeCondition]] = Field(default_factory=list)
    addresses: Optional[List[NodeAddress]] = Field(default_factory=list)
    node_info: Optional[NodeSystemInfo] = Field(None, alias="nodeInfo")
    # images: Optional[List[Any]] = None
    # volumes_in_use: Optional[List[str]] = Field(None, alias="volumesInUse")
    # volumes_attached: Optional[List[Any]] = Field(None, alias="volumesAttached")


class NodeSpec(InfraAgentBaseModel):
    """Node specification"""

    pod_cidr: Optional[str] = Field(None, alias="podCIDR")
    pod_cidrs: Optional[List[str]] = Field(None, alias="podCIDRs")
    provider_id: Optional[str] = Field(None, alias="providerId")
    unschedulable: Optional[bool] = None
    taints: Optional[List[dict]] = None


class NodeMetadata(InfraAgentBaseModel):
    """Node metadata"""

    name: str
    # creation_timestamp: Optional[datetime] = Field(None, alias="creationTimestamp")
    # deletion_timestamp: Optional[datetime] = Field(None, alias="deletionTimestamp")
    labels: Optional[dict[str, str]] = None
    annotations: Optional[dict[str, str]] = None

    # @property
    # def created_at(self) -> Optional[datetime]:
    #     """Return creation timestamp as datetime object"""
    #     return self.creation_timestamp

    # @property
    # def deleted_at(self) -> Optional[datetime]:
    #     """Return deletion timestamp as datetime object"""
    #     return self.deletion_timestamp


class Node(InfraAgentBaseModel):
    """Represents a Kubernetes node"""

    metadata: NodeMetadata
    spec: Optional[NodeSpec] = None
    status: Optional[NodeStatus] = None


class KubernetesNodeList(InfraAgentBaseModel):
    """List of Kubernetes nodes"""

    items: List[Node]


# Pod-related models
class ContainerPort(InfraAgentBaseModel):
    """Container port specification"""

    name: Optional[str] = None
    container_port: int = Field(alias="containerPort")
    protocol: Optional[str] = "TCP"


class ResourceRequirements(InfraAgentBaseModel):
    """Container resource requirements"""

    limits: Optional[Dict[str, str]] = None
    requests: Optional[Dict[str, str]] = None


class ContainerState(InfraAgentBaseModel):
    """Container state information"""

    # running: Optional[Dict[str, datetime]] = None
    # terminated: Optional[Dict[str, Any]] = None
    waiting: Optional[Dict[str, str]] = None


class ContainerStatus(InfraAgentBaseModel):
    """Container status information"""

    name: str
    state: Optional[ContainerState] = None
    last_state: Optional[ContainerState] = Field(None, alias="lastState")
    ready: bool
    restart_count: int = Field(alias="restartCount")
    image: str
    image_id: str = Field(alias="imageID")
    container_id: Optional[str] = Field(None, alias="containerID")
    started: Optional[bool] = None
    allocated_resources: Optional[Dict[str, str]] = Field(None, alias="allocatedResources")


class VolumeMount(InfraAgentBaseModel):
    """Volume mount specification"""

    name: str
    mount_path: str = Field(alias="mountPath")
    read_only: bool | None = Field(default=None, alias="readOnly")
    recursive_read_only: str | None = Field(default=None, alias="recursiveReadOnly")


class EnvVar(InfraAgentBaseModel):
    """Environment variable specification"""

    name: str
    # value: Optional[str] = None


class Container(InfraAgentBaseModel):
    """Container specification"""

    name: str
    image: str
    ports: Optional[List[ContainerPort]] = None
    env: Optional[List[EnvVar]] = None
    resources: Optional[ResourceRequirements] = None
    volume_mounts: Optional[List[VolumeMount]] = Field(None, alias="volumeMounts")
    image_pull_policy: Optional[str] = Field(None, alias="imagePullPolicy")
    security_context: Optional[Dict[str, Any]] = Field(None, alias="securityContext")
    termination_message_path: Optional[str] = Field(None, alias="terminationMessagePath")
    termination_message_policy: Optional[str] = Field(None, alias="terminationMessagePolicy")
    liveness_probe: Optional[Dict[str, Any]] = Field(None, alias="livenessProbe")
    readiness_probe: Optional[Dict[str, Any]] = Field(None, alias="readinessProbe")
    startup_probe: Optional[Dict[str, Any]] = Field(None, alias="startupProbe")


class Volume(InfraAgentBaseModel):
    """Volume specification"""

    name: str
    empty_dir: Optional[Dict[str, Any]] = Field(None, alias="emptyDir")
    host_path: Optional[Dict[str, str]] = Field(None, alias="hostPath")
    # persistent_volume_claim: Optional[Dict[str, str]] = Field(None, alias="persistentVolumeClaim")
    projected: Optional[Dict[str, Any]] = None


class NodeSelectorRequirement(InfraAgentBaseModel):
    """Node selector requirement"""

    key: str
    operator: str
    values: Optional[List[str]] = None


class NodeSelectorTerm(InfraAgentBaseModel):
    """Node selector term"""

    match_expressions: Optional[List[NodeSelectorRequirement]] = Field(None, alias="matchExpressions")
    match_fields: Optional[List[NodeSelectorRequirement]] = Field(None, alias="matchFields")


class NodeSelector(InfraAgentBaseModel):
    """Node selector"""

    node_selector_terms: List[NodeSelectorTerm] = Field(alias="nodeSelectorTerms")


class NodeAffinity(InfraAgentBaseModel):
    """Node affinity specification"""

    required_during_scheduling_ignored_during_execution: Optional[NodeSelector] = Field(
        None, alias="requiredDuringSchedulingIgnoredDuringExecution"
    )


class Affinity(InfraAgentBaseModel):
    """Affinity specification"""

    node_affinity: Optional[NodeAffinity] = Field(None, alias="nodeAffinity")


class Toleration(InfraAgentBaseModel):
    """Toleration specification"""

    key: Optional[str] = None
    operator: Optional[str] = None
    effect: Optional[str] = None
    toleration_seconds: Optional[int] = Field(None, alias="tolerationSeconds")


class PodSpec(InfraAgentBaseModel):
    """Pod specification"""

    containers: List[Container]
    volumes: Optional[List[Volume]] = None
    # affinity: Optional[Affinity] = None
    node_name: Optional[str] = Field(None, alias="nodeName")
    # service_account_name: Optional[str] = Field(None, alias="serviceAccountName")
    # service_account: Optional[str] = Field(None, alias="serviceAccount")
    restart_policy: Optional[str] = Field(None, alias="restartPolicy")
    # dns_policy: Optional[str] = Field(None, alias="dnsPolicy")
    # node_selector: Optional[Dict[str, str]] = Field(None, alias="nodeSelector")
    security_context: Optional[Dict[str, Any]] = Field(None, alias="securityContext")
    # tolerations: Optional[List[Toleration]] = None
    # priority: Optional[int] = None


class PodCondition(InfraAgentBaseModel):
    """Pod condition information"""

    type: str
    status: str
    # last_probe_time: Optional[datetime] = Field(None, alias="lastProbeTime")
    # last_transition_time: Optional[datetime] = Field(None, alias="lastTransitionTime")
    reason: Optional[str] = None
    message: Optional[str] = None


class PodIP(InfraAgentBaseModel):
    """Pod IP information"""

    ip: str


class PodStatus(InfraAgentBaseModel):
    """Pod status information"""

    conditions: Optional[List[PodCondition]] = None
    # start_time: Optional[datetime] = Field(None, alias="startTime")
    # container_statuses: Optional[List[ContainerStatus]] = Field(None, alias="containerStatuses")


class PodMetadata(InfraAgentBaseModel):
    """Pod metadata"""

    name: str
    namespace: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None


class Pod(InfraAgentBaseModel):
    """Represents a Kubernetes Pod"""

    metadata: PodMetadata
    spec: PodSpec
    status: Optional[PodStatus] = None


class KubernetesAnyList(InfraAgentBaseModel):
    """Generic Kubernetes list"""

    items: List[str]


class PodList(InfraAgentBaseModel):
    """List of Kubernetes pods"""

    items: List[Pod]


class KubernetesPodLogs(InfraAgentBaseModel):
    """Kubernetes Pod logs"""

    container_name: str
    pod_name: str
    namespace: str
    logs: List[str]


class KubernetesCapacity(InfraAgentBaseModel):
    cpu: float | None = None
    memory: str | None = None
    pods: int | None = None
    ephemeral_storage: str | None = None


class KubernetesCapacityNodeReport(InfraAgentBaseModel):
    name: str
    capacity: KubernetesCapacity | None = None
    allocatable: KubernetesCapacity | None = None


class HelmReleaseMetadata(InfraAgentBaseModel):
    """Helm release metadata extracted from Kubernetes secret"""

    name: str
    namespace: str
    chart_name: str
    default_values: str | None = None
    values: dict[str, str] | None = None
