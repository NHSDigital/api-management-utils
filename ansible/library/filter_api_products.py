#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json


def main():
    fields = {
        "products": {"default": True, "type": "str"},
        "environment": {"default": True, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields)

    products_string = module.params["products"]
    json_acceptable_string = products_string.replace("'", '"')
    products = json.loads(json_acceptable_string)
    current_env = module.params["environment"]

    for product in products:
        filtered_product = list(
            filter(lambda env: env == current_env, product["environments"])
        )
        product["environments"] = filtered_product

    module.params.update({"products": products})

    module.exit_json(changed=True, meta=module.params)


if __name__ == "__main__":
    main()
