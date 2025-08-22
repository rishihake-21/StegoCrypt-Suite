class ValidationError(ValueError):
    pass


class CapacityError(ValidationError):
    pass


class MissingDependencyError(RuntimeError):
    pass


