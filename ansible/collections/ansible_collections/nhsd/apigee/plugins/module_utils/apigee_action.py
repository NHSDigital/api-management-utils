import ansible
import pydantic
import json


class ApigeeAction(ansible.plugins.action.ActionBase):
    def validate_args(self, validator: type[pydantic.BaseModel]):
        """Returns two-length tuple of validated_args and errors dicts."""
        try:
            args = validator(**self._task.args)
            return args, {}
        except pydantic.ValidationError as e:
            return (
                None,
                {
                    "failed": True,
                    "message": f"Bad arguments to {self._task.action} in '{self._task.name}'",
                    "args": self._task.args,
                    "validation error": json.loads(e.json()),
                },
            )
