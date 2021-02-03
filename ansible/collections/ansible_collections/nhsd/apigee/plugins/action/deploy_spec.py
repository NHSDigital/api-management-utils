import json
from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.deploy_spec import (
    DeploySpec,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.apigee_action import (
    ApigeeAction,
)
from ansible_collections.nhsd.apigee.plugins.module_utils import utils
from ansible_collections.nhsd.apigee.plugins.module_utils import constants



class ActionModule(ApigeeAction):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        args, errors = self.validate_args(DeploySpec)
        if errors:
            return errors

        diff_mode = self._play_context.diff
        check_mode = self._play_context.check_mode

        task_vars = utils.get_all_spec_resources(args.organization, args.access_token, task_vars=task_vars)

        result = {
            "ansible_facts": {
                "APIGEE_SPEC_RESOURCES": task_vars["APIGEE_SPEC_RESOURCES"],
                "APIGEE_SPEC_FOLDER_ID": task_vars["APIGEE_SPEC_FOLDER_ID"],
            }
        }

        try:
            existing_resources = utils.select_unique(
                task_vars["APIGEE_SPEC_RESOURCES"],
                "name",
                args.spec.name,
            )
        except ValueError as e:
            return {
                "failed": True,
                "msg": f"Could not find unique spec resouce with name {args.spec.name}",
                "existing_resources": json.loads(str(e)),
            }

        if len(existing_resources) == 0:
            spec_resource = {
                "folder": task_vars["APIGEE_SPEC_FOLDER_ID"],
                "name": args.spec.name,
                "kind": "Doc",
            }

            if not check_mode:
                response_dict = utils.post(
                    constants.APIGEE_DAPI_URL + f"organizations/{args.organization}/specs/doc",
                    args.access_token,
                    json=spec_resource,
                )
                if response_dict.get("failed"):
                    return response_dict
                spec_resource = response_dict["response"]["body"]

            # add new spec to locally copy of all spec_resources
            task_vars["APIGEE_SPEC_RESOURCES"].insert(0, spec_resource)
            result["ansible_facts"]["APIGEE_SPEC_RESOURCES"] = task_vars[
                "APIGEE_SPEC_RESOURCES"
            ]
        else:
            spec_resource = existing_resources[0]

        result["spec_resource"] = spec_resource

        if 'id' in spec_resource:
            # Get current spec content
            spec_content_url = (
                constants.APIGEE_DAPI_URL
                + f"organizations/{args.organization}/specs/doc/{spec_resource['id']}/content"
            )
            current_spec_request = utils.get(
                spec_content_url, args.access_token, status_code=[200, 204]
            )  # returns 204 for no content
            if current_spec_request.get("failed"):
                return current_spec_request

            current_spec_content = current_spec_request["response"]["body"]
        else:
            current_spec_content = None

        new_spec_content = args.spec.content

        delta = utils.delta(current_spec_content, new_spec_content)
        result["changed"] = bool(delta)

        if diff_mode:
            result["diff"] = [
                {
                    "before_header": args.spec.name,
                    "before": current_spec_content,
                    "after_header": args.spec.name,
                    "after": new_spec_content,
                }
            ]

        if not delta or check_mode:
            result["spec_content"] = args.spec.content
            return result

        new_spec_content_request = utils.put(
            spec_content_url, args.access_token, json=new_spec_content
        )
        if new_spec_content_request.get("failed"):
            return new_spec_content_request
        utils.put(spec_content_url + "/snapshot", args.access_token)

        result["spec_content"] = new_spec_content_request["response"]["body"]
        if diff_mode:
            result["diff"][0]["after"] = result["spec_content"]

        return result
