
dexml
=====

dexml is a dead-simple object-XML mapper for Python.

To get started, check out the comprehensive :doc:`tutorial<tutorial>` or the auto-generated :doc:`API listing<api/enchant>`. If you just want to get up and running in a hurry, here's a quick sample of dexml in action::

    >>> import dexml
    >>> from dexml import fields
    >>> class Person(dexml.Model):
    ...  name = fields.String()
    ...  age = fields.Integer(tagname="age")
    ...
    >>> p = Person(name="Handsome B. Wonderful",age=36)
    >>> p.render()
  '<?xml version="1.0" ?><Person name="Handsome B. Wonderful"><age>36</age></Person>'



Documentation Index
-------------------

.. toctree::
   :maxdepth: 2

   tutorial.rst
   api/index.rst

