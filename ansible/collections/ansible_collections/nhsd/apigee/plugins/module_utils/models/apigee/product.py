import typing
import pydantic


def _literal_name(class_):
    # This accesses the 'attribute_name' from
    # class class_:
    #   name: typing.Literal['attribute_name']
    return class_.__fields__['name'].type_.__args__[0]


class ApigeeProductAttributeAccess(pydantic.BaseModel):
    name: typing.Literal["access"]
    value: typing.Literal["public", "private"]


class ApigeeProductAttributeRateLimit(pydantic.BaseModel):
    name: typing.Literal["ratelimit"]
    value: pydantic.constr(regex=r"^[0-9]+(ps|pm)$")


# This ensures that a generic ApigeeProductAttribute can't be
# constructed from a more specific one that fails valiation.
PRODUCT_ATTRIBUTE_REGEX = (
    "^(?!("
    + "|".join(
        _literal_name(c)
        for c in [
            ApigeeProductAttributeAccess,
            ApigeeProductAttributeRateLimit,
        ]
    )
    + ")$)"
)


class ApigeeProductAttribute(pydantic.BaseModel):
    name: pydantic.constr(regex=PRODUCT_ATTRIBUTE_REGEX)
    value: str


class ApigeeProduct(pydantic.BaseModel):
    name: str
    approvalType: typing.Literal["auto", "manual"]
    attributes: typing.List[
            typing.Union[
                ApigeeProductAttributeAccess,
                ApigeeProductAttributeRateLimit,
                ApigeeProductAttribute,
            ],
        ]
    description: str
    displayName: str
    environments: typing.List[str]
    proxies: typing.List[str]
    quota: str
    quotaInterval: str
    quotaTimeUnit: typing.Literal["minute", "hour"]
    scopes: typing.List[str]

    @pydantic.validator("environments", "scopes", "proxies")
    def sorted(cls, v):
        return sorted(v)

    @pydantic.validator("attributes")
    def validate_attributes(cls, attributes, values):
        attributes = sorted(attributes, key=lambda a: a.name)

        for class_ in [
            ApigeeProductAttributeAccess,
            ApigeeProductAttributeRateLimit,
        ]:
            attrs = [a for a in attributes if isinstance(a, class_)]
            if len(attrs) != 1:
                raise AssertionError(
                    f"Product {values['name']} must contain exactly 1 "
                    + f"attribute with name: '{_literal_name(class_)}', "
                    + f"found {len(attrs)}"
                )
        return attributes

    @pydantic.root_validator
    def validate_approval_type(cls, values):
        environments, approval_type = values.get("environments"), values.get("approvalType")
        if "prod" in environments and approval_type == "auto":
            raise AssertionError(
                "Product approval type must be set to 'manual'"
                + f", found '{approval_type}'"
            )
        return values
