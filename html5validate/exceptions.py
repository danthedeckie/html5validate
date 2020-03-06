class HTML5Invalid(Exception):
    pass


# class LintError(HTML5Invalid):
#    pass


class ValidationException(HTML5Invalid):
    pass


class InvalidTag(ValidationException):
    pass


class EmptyPage(ValidationException):
    pass


class MisplacedElement(ValidationException):
    pass


class MisplacedEndTag(ValidationException):
    pass


class InvalidAttribute(ValidationException):
    pass


class NonSecureRequestInSecurePage(ValidationException):
    pass


class UnclosedTags(ValidationException):
    pass


class UnknownNodeType(Exception):
    pass
