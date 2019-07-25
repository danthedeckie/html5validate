"""
    Initial tests for html5validate library.
"""

import unittest

from glob import glob
from os.path import dirname, join as pathjoin

import html5validate
from html5validate import validate, EmptyPage, ParseError, HTML5Invalid

def testfiles(test_type):
    return glob(pathjoin(dirname(__file__),'htmlfiles', test_type, '*.html'))

class TestBasic(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(EmptyPage):
            validate('')

    def test_plaintext(self):
        with self.assertRaises(ParseError):
            validate('hello world')

    def test_ptag(self):
        with self.assertRaises(ParseError):
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
    def test_unclosed_h1tag(self):
        with self.assertRaises(ParseError):
            validate('''<!doctype html><html><body><h1>hi</body></html>''')

    def test_invalid_attr(self):
        with self.assertRaises(ParseError):
            validate('''<!doctype html><html><body><h1 class"NO">hi</h1></body></html> ''')

    def test_dangling_div(self):
        with self.assertRaises(ParseError):
            validate('''<!doctype html><html><body><div>hi</body></html>''')

    def test_div_in_head(self):
        with self.assertRaises(ParseError):
            validate('''<!doctype html><html><head><div>hi</div></head></html>''')

    def test_bad_div(self):
        #validate('''<!doctype html><html><body><a href="/banana">hi</a></body></html>''')
        #validate('''<!doctype html><html><body><a gf="banana">hi</a></body></html>''')
        validate('''<!doctype html><html><body><a data-stuff="banana">hi</a></body></html>''')

class TestFromFiles(unittest.TestCase):
    def test_valid_html(self):
        files = testfiles('valid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    validate(html.read())

    def test_invalid_html(self):
        files = testfiles('invalid')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.ParseError):
                        validate(html.read())

    def test_parseerrors_html(self):
        files = testfiles('parseerrors')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.ParseError):
                        validate(html.read())

    def test_misplaced_elements(self):
        files = testfiles('misplaced_elements')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.MisplacedElement):
                        validate(html.read())

    def test_invalid_attributes(self):
        files = testfiles('invalid_attributes')
        for filename in files:
            with open(filename) as html:
                with self.subTest(f=filename):
                    with self.assertRaises(html5validate.InvalidAttribute):
                        validate(html.read())


