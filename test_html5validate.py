import unittest

from html5validate import validate, EmptyPage, ParseError, HTML5Invalid

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
