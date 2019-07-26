"""
    html5validate
    ------
    HTML5Lib based HTML5 validation module.
    MIT Licence - (C) 2019 Daniel Fairhead

"""

import html5lib

from html5lib.filters import lint, sanitizer, base

from html5lib.html5parser import ParseError

class HTML5Invalid(Exception):
    pass

class InvalideTag(HTML5Invalid):
    pass

class EmptyPage(HTML5Invalid):
    pass

#class ParseError(HTML5Invalid):
#    pass

#class LintError(HTML5Invalid):
#    pass

class ValidationException(HTML5Invalid):
    pass

class MisplacedElement(ValidationException):
    pass

class InvalidAttribute(ValidationException):
    pass

class NonSecureRequestInSecurePage(ValidationException):
    pass

class UnclosedTags(ValidationException):
    pass

# 8. Namespaces:

namespaces = {
        'html': 'http://www.w3.org/1999/xhtml',
        'mathml': "http://www.w3.org/1998/Math/MathML",
        'svg': "http://www.w3.org/2000/svg",
        'xlink': "http://www.w3.org/1999/xlink",
        'xml': "http://www.w3.org/XML/1998/namespace",
        'xmlns': "http://www.w3.org/2000/xmlns/",
        }

metadata_elements = frozenset(('base','link','meta','noscript','script','style','template','title'))

html_elements = {
# 3.2.5.2.1 "Metadata content"
    'base': ("head",),
    'link': ("head", "body"),
    'meta': ("head", "body"),
    'noscript': ("head", "body"),
    'script': ("head", "body"),
    'style': ("head", "body"),
    'template': ("head", "body"),
    'title': ("head",),

# 3.2.5.2.2 "Flow content"
    "a": ("body",),
    "abbr": ("body",),
    "address": ("body",),
    "area": ("body",),
    "article": ("body",),
    "aside": ("body",),
    "audio": ("body",),
    "b": ("body",),
    "bdi": ("body",),
    "bdo": ("body",),
    "blockquote": ("body",),
    "br": ("body",),
    "button": ("body",),
    "canvas": ("body",),
    "cite": ("body",),
    "code": ("body",),
    "data": ("body",),
    "datalist": ("body",),
    "del": ("body",),
    "details": ("body",),
    "dfn": ("body",),
    "dialog": ("body",),
    "div": ("body",),
    "dl": ("body",),
    "em": ("body",),
    "embed": ("body",),
    "fieldset": ("body",),
    "figure": ("body",),
    "footer": ("body",),
    "form": ("body",),
    "h1": ("body",),
    "h2": ("body",),
    "h3": ("body",),
    "h4": ("body",),
    "h5": ("body",),
    "h6": ("body",),
    "header": ("body",),
    "hgroup": ("body",),
    "hr": ("body",),
    "i": ("body",),
    "iframe": ("body",),
    "img": ("body",),
    "input": ("body",),
    "ins": ("body",),
    "kbd": ("body",),
    "label": ("body",),
    "li": ('ol', 'ul', 'menu'), # 4.4.8
    "main": ("body",),
    "map": ("body",),
    "mark": ("body",),
    "math": ("body",),
    "menu": ("body",),
    "meter": ("body",),
    "nav": ("body",),
    "object": ("body",),
    "ol": ("body",),
    "output": ("body",),
    "p": ("body",),
    "picture": ("body",),
    "pre": ("body",),
    "progress": ("body",),
    "q": ("body",),
    "ruby": ("body",),
    "s": ("body",),
    "samp": ("body",),
    "section": ("body",),
    "select": ("body",),
    "slot": ("body",),
    "small": ("body",),
    "source": ("video", "audio",), # embedded element
    "span": ("body",),
    "strong": ("body",),
    "sub": ("body",),
    "sup": ("body",),
    "svg": ("body",),
    "table": ("body",),
    "textarea": ("body",),
    "time": ("body",),
    "u": ("body",),
    "ul": ("body",),
    "var": ("body",),
    "video": ("body",),
    "wbr": ("body",),
}

non_recursable = frozenset(('html', 'head', 'body','video','audio'))

# 12.1.2
void_elements = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'))

# TODO: source element

def body_extra_checks(self, tag):
    # TODO.
    # 3.2.5.2.2 "Flow content"
    if tag.type == 'area':
        must_be_in('map')
    elif tag.type == 'link':
        if_allowed_in_body
    elif tag.type == 'main':
        if_hierarchically_correct_main
    elif tag.type == 'meta':
        if_present('itemprop')
    elif tag.is_autonomous_custom_element:
        pass


global_attributes = frozenset((
    # 3.2.6 - Can be for ANY
    "class",
    "id",
    "slot",
    # 3.2.6 - for HTML elements:
    "accesskey",
    "autocapitalize",
    "contenteditable",
    "dir",
    "draggable",
    "enterkeyhint",
    "hidden",
    "inputmode",
    "is",
    "itemid",
    "itemprop",
    "itemref",
    "itemscope",
    "itemtype",
    "lang",
    "nonce",
    "spellcheck",
    "tabindex",
    "title",
    "translate",
    # JS for any:
    "onabort",
    "onauxclick",
    "onblur",
    "oncancel",
    "oncanplay",
    "oncanplaythrough",
    "onchange",
    "onclick",
    "onclose",
    "oncontextmenu",
    "oncopy",
    "oncuechange",
    "oncut",
    "ondblclick",
    "ondrag",
    "ondragend",
    "ondragenter",
    "ondragexit",
    "ondragleave",
    "ondragover",
    "ondragstart",
    "ondrop",
    "ondurationchange",
    "onemptied",
    "onended",
    "onerror",
    "onfocus",
    "onformdata",
    "oninput",
    "oninvalid",
    "onkeydown",
    "onkeypress",
    "onkeyup",
    "onload",
    "onloadeddata",
    "onloadedmetadata",
    "onloadend",
    "onloadstart",
    "onmousedown",
    "onmouseenter",
    "onmouseleave",
    "onmousemove",
    "onmouseout",
    "onmouseover",
    "onmouseup",
    "onpaste",
    "onpause",
    "onplay",
    "onplaying",
    "onprogress",
    "onratechange",
    "onreset",
    "onresize",
    "onscroll",
    "onsecuritypolicyviolation",
    "onseeked",
    "onseeking",
    "onselect",
    "onstalled",
    "onsubmit",
    "onsuspend",
    "ontimeupdate",
    "ontoggle",
    "onvolumechange",
    "onwaiting",
    "onwheel",
    ))

element_attributes={
        'html': #4.1.1
            ('manifest',),
        'base': # 4.2.3
            ('href', 'target'),
        'link': #4.2.4
            ('href', 'crossorigin', 'rel', 'media', 'integrity', 'hreflang',
                'type', 'referrerpolicy', 'sizes', 'imgsrcset', 'imagesizes',
                'as', 'color'),
        'meta': # 4.2.5
            ('name', 'http-equiv', 'content', 'charset'),
        'style': # 4.2.6
            ('media',),
        'img': # 4.8.3
            ('alt', 'src', 'srcset', 'sizes', 'crossorigin', 'usemap', 'ismap',
             'width', 'height', 'referrerpolicy', 'decoding'),
        ####
        'body': # 4.3.1
            ("onafterprint",
            "onbeforeprint",
            "onbeforeunload",
            "onhashchange",
            "onlanguagechange",
            "onmessage",
            "onmessageerror",
            "onoffline",
            "ononline",
            "onpagehide",
            "onpageshow",
            "onpopstate",
            "onrejectionhandled",
            "onstorage",
            "onunhandledrejection",
            "onunload",),

        ####
        'a':
            ('href', 'target', 'download', 'ping', 'rel', 'hreflang', 'type', 'referrerpolicy'),
        ###
        'source':
            ('src', 'type', 'srcset', 'sizes', 'media'),
        'li':
            ('value',)
        }

class Validator(base.Filter):
    """
        A Validation html5lib filter / walker, which checks that elements
        are in the right places, and have the right attributes.
    """
    def __init__(self, source):
        super().__init__(source)
        self._inside = set()

    def __iter__(self):
        for token in base.Filter.__iter__(self):
            yield self.check_token(token)

        if len(self._inside):
            raise UnclosedTags(self._inside)

    def valid_element(self, token):
        token_name = token['name']
        token_type = token['type']

        if token_type == 'StartTag':
            if token_name in void_elements:
                raise InvalideTag(f"{token_name} cannot be used as a Start Tag")
            if token_name in non_recursable and token_name in self._inside:
                raise MisplacedElement(f"{token_name} cannot be inside {token_name}")
            self._inside.add(token_name)

            if token_name in ('html','head','body') and self.in_doctype:
                # Main "exclusive" sections.
                return token

        elif token_type == 'EndTag':
            if token_name in self._inside:
                self._inside.remove(token_name)
                return token
            else:
                raise MisplacedElement(f"End tag for {token_name} when not inside.")

        if not 'namespace' in token:
            if token_type == 'Doctype' and token_name == 'html':
                self.in_doctype = True
                return token
            raise ValidationException(f'No Namespace for {token}')

        try:
            required_parents = html_elements[token_name]
        except KeyError:
            raise InvalideTag(f"{token_name} is not a valid HTML5 tag.")

        if not any(parent in self._inside for parent in required_parents):
            raise MisplacedElement(f"{token_name} must be inside {required_parents}")

        return token


    def valid_attrs(self, token):
        if not 'data' in token:
            return token
        if not token['data']:
            return token

        for ((ns, k), v) in token['data'].items():
            if k in global_attributes:
                continue
            if k in element_attributes[token['name']]:
                continue
            if k.startswith('data-'):
                continue # TODO
            if k.startswith('aria-'):
                continue # TODO
            # TODO: ng-, vue-, other custom attributes?  Should be spec'd by
            #       library users.
            raise InvalidAttribute(f' {k} is not a valid attribute for {token["name"]}')


    def check_token(self, token):
        if token['type'] in ('Characters', 'SpaceCharacters'):
            return token

        self.valid_element(token)
        self.valid_attrs(token)

        return token

PARSER = html5lib.HTMLParser(html5lib.treebuilders.getTreeBuilder('dom'), strict=True)

def validate(text):
    """
        If text is valid HTML5, return None.
        Otherwise, raise some kind of Parsing or Linting Exception.
    """
    if not text.strip():
        raise EmptyPage()

    dom = PARSER.parse(text)
    walker = html5lib.getTreeWalker('dom')
    stream = walker(dom)
    # Use html5lib's lint filter first:
    lnt = lint.Filter(stream)
    [l for l in lnt]

    # Now use our checker:
    val = Validator(stream)
    [s for s in val]
