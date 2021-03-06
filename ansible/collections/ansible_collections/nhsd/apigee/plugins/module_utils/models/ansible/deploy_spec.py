import pydantic
from ansible_collections.nhsd.apigee.plugins.module_utils.models import apigee


class DeploySpec(pydantic.BaseModel):
    spec: apigee.spec.ApigeeSpec
    organization: str
    access_token: str
