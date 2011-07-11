
import sys
import os

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dexml

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.coverage',
              'hyde.ext.plugins.sphinx']

project = u'dexml'
copyright = u'2011, Ryan Kelly'

version = dexml.__version__
release = dexml.__version__

source_suffix = '.rst'
master_doc = '_sphinx_index'

