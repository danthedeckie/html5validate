from setuptools import setup

__version__ = '0.0.1'

setup(
    name='html5validate',
    py_modules=['html5validate'],
    version=__version__,
    description='Pure Python Basic HTML validatation library - for CI, django tests, etc.  Based on HTML5lib',
    long_description=open('README.rst', 'r').read(),
    long_description_content_type='text/x-rst',
    author='Daniel Fairhead',
    author_email='danthedeckie@gmail.com',
    url='https://github.com/danthedeckie/html5validate',
    download_url='https://github.com/danthedeckie/html5validate/tarball/' + __version__,
    keywords = ['html5', 'validation', 'web', 'lint'],
    test_suite='test_html5validate',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Programming Language :: Python',
                 ],
        )

