#
#  This is the dexml setuptools script.
#  Originally developed by Ryan Kelly, 2009.
#
#  This script is placed in the public domain.
#

import sys
setup_kwds = {}
if sys.version_info > (3,):
    from setuptools import setup
    setup_kwds["test_suite"] = "dexml.test"
    setup_kwds["use_2to3"] = True
else:
    from distutils.core import setup


try:
    next = next
except NameError:
    def next(i):
        return i.next()


info = {}
try:
    src = open("dexml/__init__.py")
    lines = []
    ln = next(src)
    while "__version__" not in ln:
        lines.append(ln)
        ln = next(src)
    while "__version__" in ln:
        lines.append(ln)
        ln = next(src)
    exec("".join(lines),info)
except Exception:
    pass


NAME = "dexml"
VERSION = info["__version__"]
DESCRIPTION = "a dead-simple Object-XML mapper for Python"
LONG_DESC = info["__doc__"]
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL="http://www.rfk.id.au/software/"
LICENSE = "MIT"
KEYWORDS = "xml"
CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License"
]

setup(name=NAME,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=LONG_DESC,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=["dexml"],
      classifiers=CLASSIFIERS,
      **setup_kwds
     )

