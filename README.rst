

dexml:  a dead-simple Object-XML mapper for Python
==================================================

Let's face it: xml is a fact of modern life.  I'd even go so far as to say
that it's *good* at what is does.  But that doesn't mean it's easy to work
with and it doesn't mean that we have to like it.  Most of the time, XML
just needs to get out of the way and let you do some actual work instead
of writing code to traverse and manipulate yet another DOM.

The dexml module takes the obvious mapping between XML tags and Python objects
and lets you capture that as cleanly as possible.  Loosely inspired by Django's
ORM, you write simple class definitions to define the expected structure of
your XML document.  Like so::

  >>> import dexml
  >>> from dexml import fields
  >>> class Person(dexml.Model):
  ...   name = fields.String()
  ...   age = fields.Integer(tagname='age')

Then you can parse an XML document into an object like this::

  >>> p = Person.parse("<Person name='Foo McBar'><age>42</age></Person>")
  >>> p.name
  u'Foo McBar'
  >>> p.age
  42

And you can render an object into an XML document like this::

  >>> p = Person(name="Handsome B. Wonderful",age=36)
  >>> p.render()
  '<?xml version="1.0" ?><Person name="Handsome B. Wonderful"><age>36</age></Person>'

Malformed documents will raise a ParseError::

  >>> p = Person.parse("<Person><age>92</age></Person>")
  Traceback (most recent call last):
      ...
  ParseError: required field not found: 'name'

Of course, it gets more interesting when you nest Model definitions, like this::

  >>> class Group(dexml.Model):
  ...   name = fields.String(attrname="name")
  ...   members = fields.List(Person)
  ...
  >>> g = Group(name="Monty Python")
  >>> g.members.append(Person(name="John Cleese",age=69))
  >>> g.members.append(Person(name="Terry Jones",age=67))
  >>> g.render(fragment=True)
  '<Group name="Monty Python"><Person name="John Cleese"><age>69</age></Person><Person name="Terry Jones"><age>67</age></Person></Group>'

There's support for XML namespaces, default field values, case-insensitive
parsing, and more fun stuff.  Check out the documentation on the following
classes for more details:

  :Model:  the base class for objects that map into XML
  :Field:  the base class for individual model fields
  :Meta:   meta-information about how to parse/render a model

