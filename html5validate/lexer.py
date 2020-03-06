from enum import Enum, auto
from typing import Optional, Dict, Tuple, Union, Generator, Iterator
from dataclasses import dataclass

from xml.dom import Node

WHITESPACE = "\t\r\n "  # TODO: also 0 byte? Other kinds of whitespace?


@dataclass
class TagPart:
    content: str
    start: int


"""
# This might be enough to replace the xml.dom.Node later???
class Node(Enum):
    DOCUMENT_NODE = auto()
    DOCUMENT_TYPE_NODE = auto()
    DOCUMENT_FRAGMENT_NODE = auto()

    TEXT_NODE = auto()
    CDATA_SECTION_NODE = auto()
    ELEMENT_NODE = auto()
    COMMENT_NODE = auto()
    PROCESSING_INSTRUCTION = auto()
"""

# This is the full set of attrs we use from the xml API - but we could simplify
# since we do our own tree stuff - drop the whole parent/child/sibling stuff:


class Tag:
    nodeType: Node
    parentNode: Optional["Tag"]
    firstChild: Optional["Tag"]
    nextSibling: Optional["Tag"]

    nodeValue: Optional[str] = None  # only for textNodes
    name: str
    tagName: Optional[str] = None

    has_initial_backslash: bool = False  # ... />
    has_closing_backslash: bool = False  # </ ...

    publicId: str
    systemId: str
    attributes: Dict[str, Union[str, bool]] = {}

    lineno: int
    charno: int

    def __init__(self, nodeType, **kwargs):
        self.nodeType = nodeType
        # TODO: Remove these? Are they needed?:
        self.name = kwargs.get("tagName")
        self.publicId = ""
        self.systemId = ""
        # TODO: This is lazy!
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        if self.nodeType == Node.TEXT_NODE:
            return f"TEXT:{self.nodeValue}"
        else:
            return (
                f'<{"/" if self.has_initial_backslash else ""}'
                f"Tag: {self.nodeType}"
                f' {self.tagName if self.tagName else ""},'
                f' {self.nodeValue.strip() if self.nodeValue else ""}'
                f' {self.attributes if self.attributes else ""}'
                f' {"/" if self.has_closing_backslash else ""}>'
            )


class Lexer:
    raw: str
    position: int = -1
    lineno: int = 1
    charno: int = 1
    current_char: str
    iterator: Iterator[str]
    current_item_start: Optional[int] = None

    def __init__(self, raw: str):
        self.raw = raw
        self.iterator = iter(raw)

    def advance(self) -> bool:
        """ Move forward one character """
        self.position += 1

        try:
            self.current_char = next(self.iterator)
        except StopIteration:
            return False

        if self.current_char == "\n":
            self.lineno += 1
            self.charno = 0
        else:
            self.charno += 1
        return True

    def _absorb_ws(self) -> None:
        while self.current_char in WHITESPACE:
            self.advance()

    def _read_word(self) -> str:
        word_start_pos = self.position
        while self.current_char not in WHITESPACE + "=/>":
            self.advance()
        return self.raw[word_start_pos : self.position]

    def _read_quoted(self) -> str:
        assert self.current_char in "\"'"
        start_quote = self.current_char

        self.advance()
        start_position = self.position

        while self.current_char != start_quote:
            if self.current_char == "\\":
                self.advance()
            self.advance()
        return self.raw[start_position : self.position]

    def _read_keypair(self) -> Tuple[str, Union[str, bool]]:
        key = self._read_word()
        self._absorb_ws()

        if self.current_char == "=":
            self.advance()
            self._absorb_ws()

            if self.current_char in "\"'":
                value = self._read_quoted()
                self.advance()
                return key, value
            elif self.current_char in "\>":
                return key, True
            else:
                value = self._read_word()
                if value:
                    return key, value
        return key, True

    def read_tag(self) -> Tag:
        raw = self.raw
        start_position = self.position

        has_initial_backslash = False
        has_closing_backslash = False

        self.advance()

        if self.current_char == "/":
            has_initial_backslash = True
            self.advance()

        tag_name = self._read_word()

        if tag_name[0] == "?":
            node_type = Node.PROCESSING_INSTRUCTION
            tag_name = tag_name[1:]
        elif tag_name.lower() == "!doctype":
            node_type = Node.DOCUMENT_TYPE_NODE
        else:
            node_type = Node.ELEMENT_NODE
        # TODO Should we have initial / closing backslash as separate types?

        # Comment and CDATA Nodes:

        if tag_name in ("!--", "![CDATA["):
            comment_start_position = self.position
            tag = Tag(
                Node.COMMENT_NODE if tag_name == "!--" else Node.CDATA_SECTION_NODE,
                lineno=self.lineno,
                charno=self.charno,
            )

            if tag_name == "!--":
                while raw[self.position - 3 : self.position] != "-->":
                    self.advance()
            elif tag_name == "![CDATA[":
                # TODO add CDATA tests
                while raw[self.position - 3 : self.position] != "]]>":
                    self.advance()

            tag.nodeValue = raw[comment_start_position : self.position - 3]

            return tag

        # Now get and remainder, and parse into key-value pairs...

        attributes: Dict[str, Union[str, bool]] = {}

        while True:
            self._absorb_ws()
            if self.current_char == ">":
                break
            if tag_name[0] == "?" and raw[self.position : self.position + 1] == "?>":
                self.advance()
                break

            key, value = self._read_keypair()
            if key:
                if key not in attributes:
                    attributes[key] = value
                else:
                    if key == "style":
                        print(
                            f'{self.lineno}:{self.charno} Multiple style elements in tag "{tag_name}"'
                        )
                        attributes["style"] = f'{attributes["style"]};{value}'
                    else:
                        raise Exception(
                            f"{self.lineno}:{self.charno} Attribute {key} previously used in tag '{tag_name}'"
                        )  # TODO
            else:
                break

        if self.current_char == "/":
            has_closing_backslash = True
            self.advance()

        try:
            assert raw[start_position] == "<"
            assert self.current_char == ">"
        except AssertionError:
            raise Exception(
                f'{self.lineno}:{self.charno} - Confused parsing a tag "{tag_name}"'
            )

        return Tag(
            node_type,
            tagName=tag_name,
            has_initial_backslash=has_initial_backslash,
            has_closing_backslash=has_closing_backslash,
            attributes=attributes,
            lineno=self.lineno,
            charno=self.charno,
        )

    def read_scripttag_contents(self) -> str:
        start_position = self.position

        while self.raw[self.position : self.position + 8] != "</script":
            self.advance()

        return self.raw[start_position : self.position]

    def text_node(self) -> Tag:
        return Tag(
            Node.TEXT_NODE,
            nodeValue=self.raw[self.current_item_start : self.position],
            lineno=self.lineno,
            charno=self.charno,
        )

    def __iter__(self):
        while self.advance():
            if self.current_char == "<":
                if self.raw[self.position + 1] not in WHITESPACE:
                    if (
                        self.current_item_start is not None
                        and self.current_item_start < self.position
                    ):
                        yield self.text_node()
                        self.current_item_start = None
                    tag = self.read_tag()
                    if tag.tagName == "script":
                        tag.nodeValue = self.read_scripttag_contents()
                        yield tag
                        tag = self.read_tag()  # end script tag
                    yield tag

                else:
                    if self.current_item_start is None:
                        self.current_item_start = self.position
            else:
                if self.current_item_start is None:
                    self.current_item_start = self.position

        if self.current_item_start is not None:
            yield self.text_node()