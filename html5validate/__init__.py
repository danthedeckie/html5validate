#!/usr/bin/env python3
"""
    html5validate
    ------
    HTML5Lib based HTML5 validation module.
    MIT Licence - (C) 2019 Daniel Fairhead

"""

import warnings
from collections import namedtuple
import re
from xml.dom import Node

import html5lib

from .lexer import Lexer# , Node
from . import rules

# in case we do need to track elements, here are some objects to hold them in:
DocType = namedtuple('DocType', ('name', 'publicId', 'systemId'))
StartTag = namedtuple('StartTag', ('name', 'attributes'))
VoidTag = namedtuple('VoidTag', ('name', 'attributes', 'has_children'))
EndTag = namedtuple('EndTag', ('name'))
Entity = namedtuple('Entity', ('name',))

SpaceCharacters = namedtuple('SpaceCharacters', ('data'))
Characters = namedtuple('Characters', ('data'))
Comment = namedtuple('Comment', ('data'))

# Splits <whitespace><anything><whitespace> apart.
TEXT_MATCH = re.compile(r'(\s*)(\S?.*\S)(\s*)')

from html5lib.html5parser import ParseError

class HTML5Invalid(Exception):
    pass

#class ParseError(HTML5Invalid):
#    pass

#class LintError(HTML5Invalid):
#    pass

class ValidationException(HTML5Invalid):
    pass

class InvalidTag(ValidationException):
    pass

class EmptyPage(ValidationException):
    pass

class MisplacedElement(ValidationException):
    pass

class InvalidAttribute(ValidationException):
    pass

class NonSecureRequestInSecurePage(ValidationException):
    pass

class UnclosedTags(ValidationException):
    pass

PARSER = html5lib.HTMLParser(html5lib.treebuilders.getTreeBuilder('dom'), strict=True)

class Validator:
    """
        Drills through a html5lib HTML tree, and checks all the elements
        against various rules.
    """
    def __init__(self, node_stream=None, tree=None):
        self.node_stream = node_stream
        if tree:
            self.node_stream = self.tree_to_stream(tree)
        self._in_doctype = False
        self._inside = [] # a stack of 

    def __call__(self):
        """
            Actually validate the tree.
        """

        for currentNode in self.node_stream:
            if currentNode.nodeType == Node.DOCUMENT_TYPE_NODE:
                self.doctype(currentNode.name, currentNode.publicId, currentNode.systemId)

            elif currentNode.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                self.text(currentNode.nodeValue)

            elif currentNode.nodeType == Node.ELEMENT_NODE:
                if hasattr(currentNode, 'tagName'):
                    if currentNode.tagName in rules.void_elements:
                        # TODO: what if a void el has an initial_backslash?
                        self.voidTag(currentNode.tagName, currentNode.attributes)
                    else:
                        # TODO: what if an el has_closing_backslash but isn't void?
                        # TODO: what if an el implies closing something else?
                        #       e.g. <td>in 1<td>not in 1</td>..
                        if currentNode.has_initial_backslash:
                            self.endTag(currentNode.tagName)
                        else:
                            # NEW CODE IN PROGRESS!:::: TODO TODO
                            if self._inside and self._inside[-1] in rules.implied_endtags:
                                if currentNode.tagName in rules.implied_endtags[self._inside[-1]]:
                                    self.endTag(self._inside[-1])

                            self.startTag(currentNode.tagName, currentNode.attributes)

            elif currentNode.nodeType == Node.COMMENT_NODE:
                self.comment(currentNode)

            elif currentNode.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
                self.document_node(currentNode)

            else:
                self.unknown(currentNode)

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
        if name in ('html', 'head', 'body') and not self._inside:
            return True

        try:
            required_parents = rules.html_elements[name]
        except KeyError:
            raise InvalidTag(f"{name} is not a valid HTML5 tag.")

        if not self._inside or self._inside == ['html']:
            if name in rules.metadata_elements:
                return True

        if self._inside[-1] == 'head':
            if name == 'body':
                self._inside.pop()
            elif name not in rules.metadata_elements:
                self._inside.pop()
                self._inside.append('body')
                return True

        # implicit head & body tags.
        # TODO: should there be an implicit_start rules?
        if self._inside == ['html'] and 'head' in required_parents:
            self._inside.append('head')
        elif self._inside == ['html'] and 'body' in required_parents:
            self._inside.append('body')

        if not any(parent in self._inside for parent in required_parents):
            raise MisplacedElement(f"{name} must be inside {required_parents} (currently: {self._inside})")

    def check_valid_attrs(self, name, attributes):
        case_sensitive = 'svg' in self._inside

        for (k, v) in attributes.items():
            if not case_sensitive:
                k = k.lower()
            if k in rules.global_attributes:
                continue
            if k in rules.element_attributes.get(name, ()):
                continue
            if k.startswith('data-'):
                warnings.warn("data-attributes aren't checked for validity yet")
                continue # TODO
            if k in rules.element_attribute_warnings.get(name, ()):
                warnings.warn(f"{name} should NOT have {k}={v} in HTML5.")
                continue
            if 'svg' in self._inside or name == 'svg':
                warnings.warn(f"svg attributes aren't checked for validity yet")
                continue

            #if k.startswith('aria-'):
            #    continue # TODO are there other possibilities?

            # TODO: ng-, vue-, other custom attributes?  Should be spec'd by
            #       library users.
            raise InvalidAttribute(f' {k} is not a valid attribute for {name}')

    def startTag(self, name, attributes):
        if 'svg' not in self._inside:
            name = name.lower()

        if name in rules.void_elements:
            raise InvalidTag(f"{name} cannot be used as a Start Tag")
        if name in rules.non_recursable and name in self._inside:
            raise MisplacedElement(f"{name} cannot be inside {name}")

        self.check_valid_place(name)
        self.check_valid_attrs(name, attributes)
        self._inside.append(name)

        return StartTag(name, attributes)

    def document_node(self, node):
        print('doctype!'); exit()
        self._in_doctype = True

    def endTag(self, name):
        while not self._inside[-1] == name:
            try:
                if name in rules.closed_by_parent[self._inside[-1]]:
                    self._inside.pop()
                else:
                    raise KeyError(f"{self._inside[-1]} not closed by {name}")
            except KeyError:
                raise MisplacedElement(f"End tag for {name} when not inside. (currently: {self._inside})")
        if self._inside[-1] == name:
            self._inside.pop()
        else:
            raise MisplacedElement(f"End tag for {name} when not inside. (currently: {self._inside})")

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
        raise Exception(f'Unknown! {nodeType}')




def validate(text):
    """
        If text is valid HTML5, return None.
        Otherwise, raise some kind of Parsing or Linting Exception.
    """
    if not text.strip():
        raise EmptyPage()

    dom = PARSER.parse(text)
    stream = list(Lexer(text))
    #print(stream)

    # validator = Validator(tree=dom)
    validator = Validator(node_stream=stream)
    validator()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            with open(f) as fh:
                validate(fh.read())
    else:
        validate(sys.stdin.read())
