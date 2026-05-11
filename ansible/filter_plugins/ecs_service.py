from ansible.errors import AnsibleFilterError
from ansible.plugins.filter.core import combine
from collections import Counter

_container_defaults = dict(
    cpu=0,
    port=9000,
    protocol="TCP",
    environment=[],
    mountPoints=[],
    secrets=[],
    expose=True,
    essential=True,
    health_check=dict(matcher="200", path="/"),
    lb_protocol="HTTP",
)


def as_ecs_service(docker_service):

    ecs_service = [
        combine(_container_defaults, container) for container in docker_service
    ]

    if sum(1 for _ in ecs_service if _["expose"]) != 1:
        raise AnsibleFilterError(
            "you must have exactly one exposed service, set 'expose: false' on others"
        )

    port_counts = Counter(container["port"] for container in ecs_service)

    if port_counts.get(9000, 0) != 1:
        raise AnsibleFilterError(
            "ecs_service should expose exactly one container with hostPort 9000"
        )

    for port, count in port_counts.items():
        if count > 1:
            raise AnsibleFilterError(
                f"ecs_service should not have multiple containers on the same port ({port})"
            )

    if sum(1 for _ in ecs_service if _.get("name") is None):
        raise AnsibleFilterError("all ecs containers should hava name")

    name_counts = Counter(container["name"] for container in ecs_service)

    for name, count in name_counts.items():
        if count > 1:
            raise AnsibleFilterError(
                f"ecs_service should not have multiple containers with the same name ({name})"
            )

    return ecs_service


_app_scaling_defaults = dict(
    service_metric="",
    target_value=0,
    scale_in_cooldown=300,
    scale_out_cooldown=60,
    enabled=False,
)

_ecs_service_metrics = (
    "ALBRequestCountPerTarget",
    "ECSServiceAverageCPUUtilization",
    "ECSServiceAverageMemoryUtilization",
)


def as_ecs_autoscaling(docker_service_autoscaling):

    if not docker_service_autoscaling:
        return _app_scaling_defaults

    autoscaling_policy = combine(_app_scaling_defaults, docker_service_autoscaling)
    service_metric = autoscaling_policy.get("service_metric")
    if service_metric not in _ecs_service_metrics:
        raise AnsibleFilterError(
            f"scaling policy must have a service_metric in set {_ecs_service_metrics}"
        )

    target_value = str(autoscaling_policy.get("target_value", ""))
    if not target_value.isdigit():
        raise AnsibleFilterError(
            "scaling policy must have a target_value as a positive integer"
        )

    target_value = int(target_value)
    autoscaling_policy["target_value"] = target_value
    autoscaling_policy["enabled"] = True
    if target_value < 10:
        raise AnsibleFilterError("scaling policy target_value should be >= 10")

    if service_metric == "ALBRequestCountPerTarget":
        return autoscaling_policy

    if target_value > 90:
        raise AnsibleFilterError(
            "Utilization scaling policy target_value should be between 10 and 90"
        )

    return autoscaling_policy


class FilterModule:

    @staticmethod
    def filters():
        return {
            # jinja2 overrides
            "as_ecs_service": as_ecs_service,
            "as_ecs_autoscaling": as_ecs_autoscaling,
        }
