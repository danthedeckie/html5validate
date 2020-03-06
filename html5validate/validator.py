#!/usr/bin/env python3
"""
    html5validate
    ------
    HTML5Lib based HTML5 validation module.
    MIT Licence - (C) 2019 Daniel Fairhead

"""
import logging
import warnings
from collections import namedtuple
import re
from xml.dom import Node

from .lexer import Lexer  # , Node
from . import rules

LOGGER = logging.getLogger(__name__)

# in case we do need to track elements, here are some objects to hold them in:
DocType = namedtuple("DocType", ("name", "publicId", "systemId"))
StartTag = namedtuple("StartTag", ("name", "attributes"))
VoidTag = namedtuple("VoidTag", ("name", "attributes", "has_children"))
EndTag = namedtuple("EndTag", ("name"))
Entity = namedtuple("Entity", ("name",))

SpaceCharacters = namedtuple("SpaceCharacters", ("data"))
Characters = namedtuple("Characters", ("data"))
Comment = namedtuple("Comment", ("data"))

# Splits <whitespace><anything><whitespace> apart.
TEXT_MATCH = re.compile(r"(\s*)(\S?.*\S)(\s*)")

from .exceptions import (
    HTML5Invalid,
    ValidationException,
    InvalidTag,
    EmptyPage,
    MisplacedElement,
    MisplacedEndTag,
    InvalidAttribute,
    NonSecureRequestInSecurePage,
    UnclosedTags,
    UnknownNodeType,
)


class Validator:
    """
        Runs through the nodes of a HTML tree (either from our internal lexer,
        or can take a html5lib tree) and throws exceptions when there are problems.
    """

    def __init__(self, node_stream=None, tree=None, fail_fast=True):
        self.node_stream = node_stream
        if tree:
            self.node_stream = self.tree_to_stream(tree)
        self._in_doctype = False
        self._inside = []  # a stack of tag names, that we're currently inside
        self.currentNode = None

        # Should we throw exceptions for errors, or just log them?
        self.fail_fast = fail_fast

        self.reset_errors_and_warnings()

    def reset_errors_and_warnings(self):
        self.errors = []
        self.warnings = []

    def _position_message_prefix(self):
        if self.currentNode:
            try:
                return (
                    f"{self.currentNode.lineno}"
                    f":{self.currentNode.charno}"
                    f":{'>'.join(self._inside)}"
                )

            except AttributeError:
                return f"(HTML5Lib Parser)"
        return "html5validate error"

    def _error(self, exception_type, error_message):
        if self.fail_fast:
            raise exception_type(error_message)
        else:
            LOGGER.error(f"{self._position_message_prefix()} (ERROR) - {error_message}")
            self.errors.append(
                (exception_type, self._position_message_prefix(), error_message)
            )

    def _warn(self, warning_message):
        self.has_warnings = True
        LOGGER.warning(
            f"{self._position_message_prefix()} (WARNING) - {warning_message}"
        )
        self.warnings.append((self._position_message_prefix(), warning_message))

    def __call__(self):
        """
            Actually validate the tree.
        """
        # TODO: skip this for document-fragment validation mode:
        # if self.node_stream[0].nodeType != Node.DOCUMENT_TYPE_NODE:
        #    raise HTML5Invalid("Not a HTML Document")

        for currentNode in self.node_stream:
            self.currentNode = currentNode
            if currentNode.nodeType == Node.DOCUMENT_TYPE_NODE:
                self.doctype(
                    currentNode.name, currentNode.publicId, currentNode.systemId
                )

            elif currentNode.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                self.text(currentNode.nodeValue)

            elif currentNode.nodeType == Node.ELEMENT_NODE:
                if hasattr(currentNode, "tagName"):
                    if currentNode.tagName in rules.void_elements:
                        if (
                            hasattr(currentNode, "has_initial_backslash")
                            and currentNode.has_initial_backslash
                        ):
                            self._error(
                                MisplacedEndTag,
                                f"{currentNode.tagName} is a void (contentless) element, and so shouldn't have a closing tag.",
                            )
                        # TODO - should there be a warning about has_closing_backslash and if they're needed or not?
                        self.voidTag(currentNode.tagName, currentNode.attributes)
                    elif (
                        currentNode.tagName in rules.optional_void_elements
                        and hasattr(currentNode, "has_closing_backslash")
                        and currentNode.has_closing_backslash
                    ):
                        self.voidTag(currentNode.tagName, currentNode.attributes)
                    else:
                        # TODO: what if an el has_closing_backslash but isn't void?
                        # TODO: what if an el implies closing something else?
                        #       e.g. <td>in 1<td>not in 1</td>..
                        if (
                            hasattr(currentNode, "has_initial_backslash")
                            and currentNode.has_initial_backslash
                        ):
                            self.endTag(currentNode.tagName)
                        else:
                            # NEW CODE IN PROGRESS!:::: TODO TODO
                            # TODO: This should maybe walk back from the end,
                            #       closing all possible implied end-tags?
                            #       I don't think so though.  Just think through
                            #       this again, and get soem kind of spec confirmation...
                            if (
                                self._inside
                                and self._inside[-1] in rules.implied_endtags
                            ):
                                if (
                                    currentNode.tagName
                                    in rules.implied_endtags[self._inside[-1]]
                                ):
                                    self.endTag(self._inside[-1])

                            self.startTag(currentNode.tagName, currentNode.attributes)

            elif currentNode.nodeType == Node.COMMENT_NODE:
                self.comment(currentNode)

            elif currentNode.nodeType in (
                Node.DOCUMENT_NODE,
                Node.DOCUMENT_FRAGMENT_NODE,
            ):
                self.document_node(currentNode)

            else:
                self.unknown(currentNode)

        return False if self.errors else True

    def tree_to_stream(self, dom):
        currentNode = dom
        while True:
            if currentNode.firstChild:
                currentNode = currentNode.firstChild
            elif currentNode.nextSibling:
                currentNode = currentNode.nextSibling
            elif currentNode.parentNode.nextSibling:
                self.endTag(currentNode.parentNode.tagName)
                currentNode = currentNode.parentNode.nextSibling
            else:
                break

            if currentNode == dom:
                break

            yield currentNode

    def check_valid_place(self, name):
        if name in ("html", "head", "body") and not self._inside:
            return True

        if not "svg" in self._inside:
            name = name.lower()

        try:
            required_parents = rules.html_elements[name]
        except KeyError:
            self._error(InvalidTag, f"{name} is not a valid HTML5 tag.")

        if not self._inside or self._inside == ["html"]:
            if name in rules.metadata_elements:
                return True

        if self._inside[-1] == "head":
            if name == "body":
                self._inside.pop()
            elif name not in rules.metadata_elements:
                self._inside.pop()
                self._inside.append("body")
                return True

        # implicit head & body tags.
        # TODO: should there be an implicit_start rules?
        if self._inside == ["html"] and "head" in required_parents:
            self._inside.append("head")
        elif self._inside == ["html"] and "body" in required_parents:
            self._inside.append("body")

        if not any(parent in self._inside for parent in required_parents):
            self._error(MisplacedElement, f"{name} must be inside {required_parents}")

    def check_valid_attrs(self, name, attributes):
        case_sensitive = "svg" in self._inside

        for (k, v) in attributes.items():
            if not case_sensitive:
                k = k.lower()

            if k in rules.global_attributes:
                continue
            if k in rules.element_attributes.get(name, ()):
                continue
            if k.startswith("data-"):
                self._warn("data-attributes aren't checked for validity yet")
                continue  # TODO
            if k in rules.element_attribute_warnings.get(name, ()):
                self._warn(f"{name} should NOT have {k}={v} in HTML5.")
                continue
            if "svg" in self._inside or name == "svg":
                self._warn(f"svg attributes aren't checked for validity yet")
                continue

            # if k.startswith('aria-'):
            #    continue # TODO are there other possibilities?

            # TODO: ng-, vue-, other custom attributes?  Should be spec'd by
            #       library users.
            self._error(InvalidAttribute, f'"{k}" is not a valid attribute for {name}')

    def startTag(self, name, attributes):
        if "svg" not in self._inside:
            name = name.lower()

        if name in rules.void_elements:
            self._error(InvalidTag, f"{name} cannot be used as a Start Tag")
        if name in rules.non_recursable and name in self._inside:
            self._error(MisplacedElement, f"{name} cannot be inside {name}")

        self.check_valid_place(name)
        self.check_valid_attrs(name, attributes)
        self._inside.append(name)

        return StartTag(name, attributes)

    def document_node(self, node):
        self._in_doctype = True

    def endTag(self, name):
        if not "svg" in self._inside:
            name = name.lower()

        while not self._inside[-1] == name:
            try:
                if name in rules.closed_by_parent[self._inside[-1]]:
                    self._inside.pop()
                else:
                    raise KeyError(f"{self._inside[-1]} not closed by {name}")
            except KeyError:
                if name in self._inside:
                    self._error(
                        MisplacedEndTag,
                        f"End tag for '{name}' while other elements ({self._inside}) still open",
                    )
                else:
                    self._error(MisplacedEndTag, f"End tag for {name} when not inside")
        if self._inside[-1] == name:
            self._inside.pop()
        else:
            self._error(MisplacedEndTag, f"End tag for {name} when not inside")

        self.check_valid_place(name)
        return EndTag(name)

    def voidTag(self, name, attrs, hasChildren=False):
        self.check_valid_place(name)
        self.check_valid_attrs(name, attrs)

        return VoidTag(name, attrs, hasChildren)

    def text(self, data):
        try:
            prefix, mid, suffix = TEXT_MATCH.match(data).groups()
        except AttributeError:
            yield Characters(data)
            return

        if prefix:
            yield SpaceCharacters(prefix)
        if mid:
            yield Characters(mid)
            if suffix:
                yield SpaceCharacters(suffix)

    def comment(self, data):
        return Comment(data)

    def doctype(self, name, publicId=None, systemId=None):
        self._in_doctype = True
        return DocType(name, publicId, systemId)

    def unknown(self, nodeType):
        self._error(UnknownNodeType, f"Unknown! {nodeType}")


def validate(text):
    """
        If text is valid HTML5, return None.
        Otherwise, raise some kind of Parsing or Linting Exception.
    """
    if not text.strip():
        raise EmptyPage()

    stream = list(Lexer(text))

    # validator = Validator(tree=dom)
    validator = Validator(node_stream=stream)
    validator()
