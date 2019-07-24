HTML5Validate
========================

.. image:: https://travis-ci.org/danthedeckie/html5validate.svg?branch=master
   :target: https://travis-ci.org/danthedeckie/html5validate
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/danthedeckie/html5validate/badge.svg?branch=master
   :target: https://coveralls.io/r/danthedeckie/html5validate?branch=master
   :alt: Coverage Status

.. image:: https://badge.fury.io/py/html5validate.svg
   :target: https://badge.fury.io/py/html5validate
   :alt: PyPI Version

HTML5 text validation, provided by HTML5lib.  Designed to integrate easily in
django or other web development environments, to ensure templates actually render
as intented, without dangling tags, or other nonsense.

Currently just uses HTML5lib's parsing and linting, which is enough for me
right now - it would be nice to have some more comprehensive checking, and
possibly even write some valid-attribute checking - although that's a BIG
project.

Usage:
------

.. code-block:: python

   >>> from html5validate import validate
   >>> validate('<!doctype html><html><body><h1>Hi World!</h1></body></html>')
   None
   >>> validate('<!doctype html><html><body><h1>Hi World!</body></html>')
   Traceback (most recent call last):
   ...
   html5lib.html5parser.ParseError: Expected closing tag. Unexpected end of file.


So.  You run 'validate' on some text, and it either returns None, or throws
some kind of error at you.

With Django in tests:
---------------------

.. code-block:: python

   from django.test import TestCase
   from html5validate import validate

   class TestIndexViewValid(TestCase):
      def test_basic_index(self):
         validate(self.client.get(reverse('index'), follow=True))


Status:
-------

Very Early - I just pulled this out of some django view testing code in one of
my other projects, as it seemed more sensible to have it as a stand-alone
library that could be unit-tested and stuff, and I can use again easily.

Initial basic tests are here - but it should really have a LOT of tests written.

Roadmap:
--------

- Write a bunch of tests to see how strict it really is.
- Write some extra tree walkers and checkers to look for valid tags, and throw
  some decent exceptions, and have customisability, specify what tags users
  want, etc.


