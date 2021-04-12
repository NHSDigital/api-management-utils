import requests
import json
import bisect
import copy

from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.add_jwks_resource_url import (
    AddJwksResourceUrlToApp,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.apigee_action import (
    ApigeeAction,
)
from ansible_collections.nhsd.apigee.plugins.module_utils import utils
from ansible_collections.nhsd.apigee.plugins.module_utils import constants

ATTRIBUTE_NAME = "jwks-resource-url"
DEVELOPER_DETAILS = "APIGEE_DEVELOPER_DETAILS"


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
        after["attributes"] = [
            attr for attr in after["attributes"] if attr["name"] != ATTRIBUTE_NAME
        ]
        # Append the desired jwks attributes and sort
        after["attributes"].append(jwks_attribute)
        after["attributes"] = sorted(after["attributes"], key=lambda attr: attr["name"])

        developer_details = task_vars.get(DEVELOPER_DETAILS)
        if not developer_details:
            url = (
                constants.APIGEE_BASE_URL
                + f"organizations/{args.organization}/developers?expand=true"
            )
            resp = utils.get(url, args.access_token)
            if resp.get("failed"):
                return resp
            developer_details = resp["response"]["body"]["developer"]
        try:
            i = bisect.bisect_left(
                [d["developerId"] for d in developer_details],
                args._app_data["developerId"],
            )
        except RuntimeError as e:
            return json.loads(str(e))
        developer = developer_details[i]

        delta = utils.delta(before, after)
        result = {
            "changed": bool(delta),
            "app": after,
            "developer": developer,
            "ansible_facts": {DEVELOPER_DETAILS: developer_details},
        }

        app_name = args._app_data["name"]
        app_path = f"organizations/{args.organization}/developers/{developer['email']}/apps/{app_name}/attributes"

        if diff_mode:
            result["diff"] = [
                {
                    "before": before,
                    "before_header": app_path,
                    "after": after,
                    "after_header": app_path,
                }
            ]

        if check_mode:
            return result

        app_attribute_url = constants.APIGEE_BASE_URL + app_path

        app_data2 = utils.post(
            app_attribute_url,
            args.access_token,
            json={"attribute": after["attributes"]},
        )
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
