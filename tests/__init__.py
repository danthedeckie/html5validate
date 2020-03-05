"""
    Initial tests for html5validate library.
"""

import unittest

from glob import glob
from os.path import dirname, join as pathjoin

import html5validate.exceptions
from html5validate.validator import validate, Validator

import html5lib

def findfiles(test_type):
    return glob(pathjoin(dirname(__file__),'htmlfiles', test_type, '*.html'))

class TestBasic(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(html5validate.exceptions.EmptyPage):
            validate('')

    @unittest.skip # TODO
    def test_plaintext(self):
        with self.assertRaises(html5validate.exceptions.HTML5Invalid):
            validate('hello world')

    @unittest.skip # TODO
    def test_ptag(self):
        with self.assertRaises(html5validate.exceptions.HTML5Invalid):
            validate('<p>Hello!</p>')

    def test_valid_basic(self):
        validate('''<!doctype html>
        <html>
        <head>
        <title>Test Page</title>
        </head>
        <body>
        <h1>Hello!</h1>
        </body>
        </html>
        ''')

class TestBrokenHTML(unittest.TestCase):
    # TODO - move these tests out to proper files...

    def test_unclosed_h1tag(self):
        with self.assertRaises(html5validate.exceptions.MisplacedEndTag):
            validate('''<!doctype html><html><body><h1>hi</body></html>''')

    def test_invalid_attr(self):
        with self.assertRaises(html5validate.exceptions.InvalidAttribute):
            validate('''<!doctype html><html><body><h1 class"NO">hi</h1></body></html> ''')

    def test_dangling_div(self):
        with self.assertRaises(html5validate.exceptions.MisplacedEndTag):
            validate('''<!doctype html><html><body><div>hi</body></html>''')

    def test_div_in_head(self):
        with self.assertRaises(html5validate.exceptions.MisplacedEndTag):
            # This is a 'misplaced_endtag' because a <div> automatically closes
            # the head. TODO: make an edge-case checker for this that gives a
            # more helpful explanation.
            validate('''<!doctype html><html><head><div>hi</div></head></html>''')

    def test_bad_div(self):
        #validate('''<!doctype html><html><body><a href="/banana">hi</a></body></html>''')
        #validate('''<!doctype html><html><body><a gf="banana">hi</a></body></html>''')
        validate('''<!doctype html><html><body><a data-stuff="banana">hi</a></body></html>''')

class TestFromFiles(unittest.TestCase):
    def test_valid_html(self):
        files = findfiles('valid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    validate(html.read())

    def test_invalid_html(self):
        files = findfiles('invalid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.exceptions.ValidationException):
                        validate(html.read())

    def test_misplaced_elements(self):
        files = findfiles('misplaced_elements')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.exceptions.MisplacedElement):
                        validate(html.read())

    def test_misplaced_endtags(self):
        files = findfiles('misplaced_endtags')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.exceptions.MisplacedEndTag):
                        validate(html.read())

    def test_invalid_attributes(self):
        files = findfiles('invalid_attributes')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.exceptions.InvalidAttribute):
                        validate(html.read())


class TestHTML5LibParser(unittest.TestCase):
    def setUp(self):
        self.parser = html5lib.HTMLParser(html5lib.treebuilders.getTreeBuilder('dom'), strict=True)

    def validate(self, text):
        Validator(tree=self.parser.parse(text))()

    def test_valid_html(self):
        files = findfiles('valid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    self.validate(html.read())

    def test_invalid_html(self):
        files = findfiles('invalid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises((html5lib.html5parser.ParseError, html5validate.exceptions.ValidationException)):
                        self.validate(html.read())

    def test_misplaced_elements(self):
        files = findfiles('misplaced_elements')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises((html5lib.html5parser.ParseError, html5validate.exceptions.MisplacedElement)):
                        self.validate(html.read())

    def test_misplaced_endtags(self):
        files = findfiles('misplaced_endtags')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises((html5lib.html5parser.ParseError, html5validate.exceptions.MisplacedEndTag)):
                        self.validate(html.read())

    def test_invalid_attributes(self):
        files = findfiles('invalid_attributes')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises((html5lib.html5parser.ParseError, html5validate.exceptions.InvalidAttribute)):
                        self.validate(html.read())


