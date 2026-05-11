from lxml import etree
import tempfile

from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.add_policy_to_pre_flow import (
    AddPolicyToPreFlow,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.apigee_action import (
    ApigeeAction,
)


def find_or_make_child_element(element: etree.Element, element_name: str):
    result = element.find(element_name)
    if result is None:
        child = etree.Element(element_name)
        element.append(child)
        result = element.find(element_name)
    return result


class ActionModule(ApigeeAction):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        args, errors = self.validate_args(AddPolicyToPreFlow)
        if errors:
            return errors

        diff_mode = self._play_context.diff
        check_mode = self._play_context.check_mode

        # Now we have the policy file, add a call into preflow/requests
        proxies_dir = args.dist_dir.joinpath(
            "proxies", args.proxy_dir, "apiproxy/proxies"
        )
        proxies_files = [f for f in proxies_dir.glob("*.xml")]

        if len(proxies_files) != 1:
            return {
                "failed": True,
                "msg": f"Unable to local proxy definition file in {str(proxies_dir)}",
            }

        proxies_file = proxies_files[0]

        tree = etree.parse(str(proxies_file), etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        pre_flow = find_or_make_child_element(root, "PreFlow")
        request = find_or_make_child_element(pre_flow, "Request")

        steps = request.findall("Step")

        # Guard against adding it twice,
        # which should never happen but is
        # useful for testing.
        for step in steps:
            name = step.find("Name")
            if name.text == args.policy_name:
                return {"changed": False}

        result = {"changed": True}
        if diff_mode:
            result["diff"] = {
                "before": etree.tostring(tree, pretty_print=True).decode(),
                "before_header": str(proxies_file),
            }

        step = etree.Element("Step")
        request.append(step)
        name = step.makeelement("Name")
        name.text = args.policy_name
        step.append(name)

        if diff_mode:
            result["diff"].update(
                {
                    "after": etree.tostring(tree, pretty_print=True).decode(),
                    "after_header": str(proxies_file),
                }
            )

        if check_mode or result["changed"] is False:
            return result

        tree.write(str(proxies_file), pretty_print=True)

        return result
