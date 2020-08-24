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
    health_check=dict(
        matcher="200",
        path="/"
    ),
    lb_protocol="HTTP"

)


def as_ecs_service(docker_service):

    ecs_service = [combine(_container_defaults, container) for container in docker_service]

    if sum(1 for _ in ecs_service if _["expose"]) != 1:
        raise AnsibleFilterError("you must have exactly one exposed service, set 'expose: false' on others")

    port_counts = Counter(container['port'] for container in ecs_service)

    if port_counts.get(9000, 0) != 1:
        raise AnsibleFilterError("ecs_service should expose exactly one container with hostPort 9000")

    for port, count in port_counts.items():
        if count > 1:
            raise AnsibleFilterError(f"ecs_service should not have multiple containers on the same port ({port})")

    if sum(1 for _ in ecs_service if _.get('name') is None):
        raise AnsibleFilterError("all ecs containers should hava name")

    name_counts = Counter(container['name'] for container in ecs_service)

    for name, count in name_counts.items():
        if count > 1:
            raise AnsibleFilterError(f"ecs_service should not have multiple containers with the same name ({name})")

    return ecs_service


class FilterModule:

    @staticmethod
    def filters():
        return {
            # jinja2 overrides
            'as_ecs_service': as_ecs_service
        }

