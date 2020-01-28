from enum import Enum, auto
from typing import Optional, Dict, Tuple, Union, Generator
from dataclasses import dataclass

WHITESPACE = '\t\r\n '

@dataclass
class TagPart:
    content: str
    start: int

class Node(Enum):
    DOCUMENT_NODE = auto()
    DOCUMENT_TYPE_NODE = auto()
    DOCUMENT_FRAGMENT_NODE = auto()

    TEXT_NODE = auto()
    CDATA_SECTION_NODE = auto()
    ELEMENT_NODE = auto()
    COMMENT_NODE = auto()
    PROCESSING_INSTRUCTION = auto()

# This is the full set of attrs we use from the xml API - but we could simplify
# since we do our own tree stuff - drop the whole parent/child/sibling stuff:

class Tag:
    nodeType: Node
    parentNode: Optional['Tag']
    firstChild: Optional['Tag']
    nextSibling: Optional['Tag']

    nodeValue: Optional[str] = None # only for textNodes
    name: str
    tagName: Optional[str] = None

    has_initial_backslash: bool = False # ... />
    has_closing_backslash: bool = False # </ ...

    publicId: str
    systemId: str
    attributes: Dict[str, str] = {}

    lineno: int
    charno: int

    def __init__(self, nodeType, **kwargs):
        self.nodeType = nodeType
        # TODO: This is lazy!
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Tag: {self.nodeType} {self.tagName if self.tagName else ""}, {self.nodeValue if self.nodeValue else ""} {self.attributes}>'

def read_tag(raw: str, start_position: int) -> Tuple[Tag, int]:
    """
    In a larger "raw" blob of html, starting from "start_position", read
    a HTML Tag.  Return that Tag, and how far many characters were read.
    """
    has_initial_backslash = False
    has_closing_backslash = False

    end_position = start_position + 1

    if raw[end_position] == '/':
        has_initial_backslash = True
        end_position += 1

    while raw[end_position] not in WHITESPACE + '/>':
        end_position += 1

    if raw[end_position] == '/':
        has_closing_backslash = True
        end_position += 1

    if raw[start_position+1] == '?':
        node_type = Node.PROCESSING_INSTRUCTION
    elif raw[start_position:9] == '<!doctype':
        node_type = Node.DOCUMENT_TYPE_NODE
    else:
        node_type = Node.ELEMENT_NODE
    # TODO Should we have initial / closing backslash as separate types?

    tag_name = raw[start_position+1 + (1 if has_initial_backslash else 0)
                  : end_position - (1 if has_closing_backslash else 0)]


    # Comment and CDATA Nodes:

    if tag_name == '!--':
        while raw[end_position-3:end_position] != '-->':
            end_position += 1
        return Tag(Node.COMMENT_NODE), end_position - start_position

    if tag_name == '![CDATA[':
        while raw[end_position-3:end_position] != ']]>':
            end_position += 1
        return Tag(Node.CDATA_SECTION_NODE), end_position - start_position


    # Now get and remainder, and parse into key-value pairs...

    def absorb_ws():
        nonlocal end_position
        while raw[end_position] in WHITESPACE:
            end_position += 1

    def read_word():
        nonlocal end_position
        word_start_pos = end_position
        while raw[end_position] not in WHITESPACE + '=/>':
            end_position += 1
        return raw[word_start_pos:end_position]

    def read_quoted():
        nonlocal end_position
        assert raw[end_position] in '"\''
        start_quote = raw[end_position]
        end_position += 1
        while raw[end_position] != start_quote:
            if raw[end_position] == '\'':
                end_position += 1
            end_position += 1

    def read_keypair():
        nonlocal end_position
        absorb_ws()
        if raw[end_position] == '>':
            return None, None
        if tag_name[0] == '?' and raw[end_position:end_position+1] == '?>':
            end_position +=1
            return None, None
        key = read_word()
        absorb_ws()
        if raw[end_position] == '=':
            end_position += 1
            absorb_ws()
            if raw[end_position] in '"\'':
                value = read_quoted()
                end_position += 1
                return key, value
            elif raw[end_position] in '\>':
                return key, True
        return key, True

    attributes: Dict[str, Union[str, bool]] = {}

    while True:
        key, value = read_keypair()
        if key:
            if key not in attributes:
                attributes[key] = value
            else:
                raise Exception("KEY USED TOO MANY TIMES!!!!") # TODO
        else:
            break

    if raw[end_position] == '/':
        has_closing_backslash = True
        end_position += 1

    assert raw[start_position] == '<'
    assert raw[end_position] == '>'

    tag = Tag(node_type, tagName=tag_name, has_initial_backslash=has_initial_backslash, has_closing_backslash=has_closing_backslash, attributes=attributes)
    return tag, end_position - start_position

def parse_str(raw: str) -> Generator[Tag, None, None]:
    lineno = 0
    charno = 0

    current_text_start = None

    i = -1

    def text_node():
        return Tag(Node.TEXT_NODE, nodeValue=raw[current_text_start: i], lineno=lineno, charno=charno)

    while i < len(raw):
        i += 1
        try:
            c = raw[i]
        except IndexError:
            if current_text_start is not None:
                yield text_node()
            return

        if c == '\n':
            lineno += 1
            charno = 0
        else:
            charno += 1

        if c == '<':
            if raw[i + 1] != ' ':
                if current_text_start is not None and current_text_start < i:
                    yield text_node()
                    current_text_start = None
                tag, length = read_tag(raw, i)
                yield tag
                i += length
            else:
                if current_text_start is None:
                    current_text_start = i
        else:
            if current_text_start is None:
                current_text_start = i

