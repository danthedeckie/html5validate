from enum import Enum, auto
from typing import Optional, Dict

class Node(Enum):
    DOCUMENT_NODE = auto()
    DOCUMENT_TYPE_NODE = auto()
    DOCUMENT_FRAGMENT_NODE = auto()

    TEXT_NODE = auto()
    CDATA_SECTION_NODE = auto()
    ELEMENT_NODE = auto()
    # TODO Start and End tags?  Or Here (lexer) just say tag and be done?
    COMMENT_NODE = auto()

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

def read_tag(raw, start_position):
    end_position = start_position
    #TODO: this is not right!
    while raw[end_position] != '>':
        end_position += 1

    assert raw[start_position] == '<'
    assert raw[end_position] == '>'

    # TODO this is also not right, and needs a char-by-char parser
    # TODO: asserts should be replaced with proper error messages
    attributes = {}
    lumps = raw[start_position + 1: end_position].split(' ')
    for lump in lumps[1:]:
        if '=' in lump:
            key, value = lump.split('=') # TODO: what if '=' in value?
            if value.startswith('"') or value.startswith("'"):
                if not value[0] == value[-1]:
                    print(value)
                value = value[1:-1]
            assert key not in attributes
        else:
            key=lump
            value=True
        attributes[key] = value

    tag = Tag(Node.ELEMENT_NODE, tagName=lumps[0], attributes=attributes)
    return tag, end_position - start_position

def parse_str(raw):
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

