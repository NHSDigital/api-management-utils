import json

import pytest

from ansible_collections.nhsd.apigee.plugins.module_utils.models.apigee.product import (
    ApigeeProduct,
)


def _make_product_dict(name, environment="internal-dev", approval_type="auto"):
    return {
        "name": f"{name}-{environment}",
        "approvalType": approval_type,
        "attributes": [
            {"name": "access", "value": "public"},
            {"name": "ratelimit", "value": "300pm"},
        ],
        "description": "testing our validators",
        "displayName": "Test Product",
        "environments": [environment],
        "proxies": [f"{name}-{environment}", f"identity-service-{environment}"],
        "scopes": [
            f"urn:nhsd:apim:app:level3:{name}",
            f"urn:nhsd:apim:user-nhs-login:P9:{name}",
        ],
        "quota": "300",
        "quotaInterval": "1",
        "quotaTimeUnit": "minute",
    }


@pytest.mark.parametrize(
    "env,initial_approvaltype,final_approvaltype",
    [
        ("prod", "auto", "manual"),
        ("prod", "manual", "manual"),
        ("int", "auto", "auto"),
        ("int", "manual", "manual"),
    ],
)
def test_prod_cannot_have_auto_approvaltype_on_products(
    env, initial_approvaltype, final_approvaltype
):
    product_dict = _make_product_dict(
        "test-service", environment=env, approval_type=initial_approvaltype
    )
    product = ApigeeProduct(**product_dict)
    assert product.approvalType == final_approvaltype


@pytest.mark.parametrize(
    "name,env,initial_approvaltype,final_approvaltype",
    [
        ("canary-api", "prod", "auto", "auto"),
        ("canary-api", "prod", "manual", "manual"),
        ("non-exception-product", "prod", "auto", "manual"),
        ("non-exception-product", "prod", "manual", "manual"),
    ],
)
def test_manual_approval_exception_list_on_prod(
    name, env, initial_approvaltype, final_approvaltype
):
    product_dict = _make_product_dict(
        name, environment=env, approval_type=initial_approvaltype
    )
    product = ApigeeProduct(**product_dict)
    assert product.approvalType == final_approvaltype


def test_ratelimiting_product_attribute_initialized_with_dict_or_string():
    product_dict = _make_product_dict("test-service")

    ratelimiting_dict = {
        "quota": {"enabled": True, "interval": 1, "timeunit": "minute", "limit": 300},
        "spikeArrest": {"ratelimit": "30000pm"},  # 5000 tps
    }
    attr_dict = {product_dict["name"]: ratelimiting_dict}

    # Init with dict-like
    product_dict["attributes"].append({"name": "ratelimiting", "value": attr_dict})
    product1 = ApigeeProduct(**product_dict)

    # Assert ratelimiting attribute gets serialized to a string
    assert isinstance(product1.attributes[-1].value, str)

    # Init with attribute values already a string
    attr_str = json.dumps(attr_dict)
    product_dict["attributes"][-1]["value"] = attr_str
    product2 = ApigeeProduct(**product_dict)

    # Should be the same
    assert product1.attributes[-1].value == product2.attributes[-1].value
