import copy
from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.add_jwks_resource_url import (
    AddJwksResourceUrlToApp
)
from ansible_collections.nhsd.apigee.plugins.module_utils.apigee_action import (
    ApigeeAction,
)
from ansible_collections.nhsd.apigee.plugins.module_utils import utils
from ansible_collections.nhsd.apigee.plugins.module_utils import constants


ATTRIBUTE_NAME = "jwks-resource-url"


class ActionModule(ApigeeAction):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        args, errors = self.validate_args(AddJwksResourceUrlToApp)
        if errors:
            return errors

        diff_mode = self._play_context.diff
        check_mode = self._play_context.check_mode

        before = args._app_data
        after = copy.deepcopy(before)

        jwks_attribute = {"name": ATTRIBUTE_NAME, "value": str(args.jwks_resource_url)}

        # Delete any existing jwks attributes, for now there can only be one.
        after["attributes"] = [attr for attr in after["attributes"] if attr["name"] != ATTRIBUTE_NAME]
        # Append the desired jwks attributes and sort
        after["attributes"].append(jwks_attribute)
        after["attributes"] = sorted(after["attributes"], key=lambda attr: attr["name"])

        delta = utils.delta(before, after)
        result = {"changed": bool(delta), "app": after}

        if diff_mode:
            result["diff"] = [{"before": before, "after": after}]

        if check_mode:
            return result

        developer_email = args._app_data["createdBy"]
        app_name = args._app_data["name"]
        app_attribute_url = (
            constants.APIGEE_BASE_URL
            + f"organizations/{args.organization}/developers/{developer_email}/apps/{app_name}/attributes"
        )
        app_data2 = utils.post(app_attribute_url, args.access_token,
                               json={"attribute": after["attributes"]})
        if app_data2.get("failed"):
            return app_data2

        app_url = (
            constants.APIGEE_BASE_URL
            + f"organizations/{args.organization}/apps/{args.app_id}"
        )
        updated_app_response = utils.get(app_url, args.access_token)
        if updated_app_response.get("failed"):
            return updated_app_response

        after = updated_app_response["response"]["body"]
        if diff_mode:
            result["diff"][-1]["after"] = after

        result["app"] = after
        return result
