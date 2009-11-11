#
#  This is the dexml setuptools script.
#  Originally developed by Ryan Kelly, 2009.
#
#  This script is placed in the public domain.
#

from distutils.core import setup

import dexml
VERSION = dexml.__version__

NAME = "dexml"
DESCRIPTION = "a dead-simple Object-XML mapper for Python"
LONG_DESC = dexml.__doc__
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL="http://www.rfk.id.au/software/"
LICENSE = "MIT"
KEYWORDS = "xml"

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
     )

