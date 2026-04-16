from typing import Annotated, Any, get_args, get_origin, get_type_hints


class NumberConstraints:
    """Represents numeric validation constraints for a field.

    Supports inclusive and exclusive bounds:
        - ge: greater than or equal to
        - le: less than or equal to
        - gt: strictly greater than
        - lt: strictly less than
    """

    def __init__(
        self,
        ge: float | None = None,
        le: float | None = None,
        gt: float | None = None,
        lt: float | None = None,
    ) -> None:
        """Initialize numeric constraints.

        Args:
            ge: Minimum value (inclusive). Value must be >= ge.
            le: Maximum value (inclusive). Value must be <= le.
            gt: Minimum value (exclusive). Value must be > gt.
            lt: Maximum value (exclusive). Value must be < lt.
        """
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt

    def validate(self, field_name: str, value: int | float) -> None:
        """Validate a numeric value against the defined constraints.

        Args:
            field_name (str): Name of the field being validated.
            value (int | float): The numeric value to validate.

        Raises:
            TypeError: If the value is not an int or float.
            ValueError: If the value violates any of the constraints.
        """

        if not isinstance(value, (int, float)):
            raise TypeError(f"{field_name} must be a number")

        if self.ge is not None and value < self.ge:
            raise ValueError(f"{field_name} must be >= {self.ge}")

        if self.le is not None and value > self.le:
            raise ValueError(f"{field_name} must be <= {self.le}")

        if self.gt is not None and value <= self.gt:
            raise ValueError(f"{field_name} must be > {self.gt}")

        if self.lt is not None and value >= self.lt:
            raise ValueError(f"{field_name} must be < {self.lt}")


def validate_constraints(obj: Any) -> None:
    """Validate all Annotated fields on an object using attached constraint metadata.

    This function inspects type hints (including Annotated metadata) and applies
    any constraint object that provides a callable `validate` method.

    Expected usage:
        class Example:
            x: Annotated[int, NumberConstraints(ge=0, le=10)]

    Args:
        obj (Any): The object whose fields should be validated.

    Raises:
        Any exception raised by constraint validation (e.g., TypeError, ValueError).
    """

    # Retrieve type hints with metadata (Annotated included)
    type_hints = get_type_hints(obj, include_extras=True)

    for field_name, type_hint in type_hints.items():

        # Check if the field uses Annotated[...] typing
        if get_origin(type_hint) is Annotated:

            # Get the actual field value from the object
            value = getattr(obj, field_name)

            # Extract the constraint metadata (assumes second argument of Annotated)
            constraint = get_args(type_hint)[1]

            # Extract the constraint metadata (assumes second argument of Annotated)
            validate = getattr(constraint, "validate", None)
            if callable(validate):
                validate(field_name, value)
