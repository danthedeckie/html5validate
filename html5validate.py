import html5lib
from html5lib.filters import lint

from html5lib.html5parser import ParseError

class HTML5Invalid(Exception):
    pass

class EmptyPage(HTML5Invalid):
    pass

#class ParseError(HTML5Invalid):
#    pass

#class LintError(HTML5Invalid):
#    pass

PARSER = html5lib.HTMLParser(html5lib.treebuilders.getTreeBuilder('dom'), strict=True)

def validate(text):
    if not text.strip():
        raise EmptyPage()

    dom = PARSER.parse(text)

    walker = html5lib.getTreeWalker('dom')
    stream = walker(dom)
    lnt = lint.Filter(stream)
