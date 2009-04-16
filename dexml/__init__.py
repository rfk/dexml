"""

  dexml:  xml processing for people who hate processing xml

"""

from xml.dom import minidom
from dexml import fields

class Error(Exception):
    pass

class ParseError(Error):
    pass

class RenderError(Error):
    pass

class XmlError(Error):
    pass


class Meta:
    """Class holding meta-information about a class."""

    def __init__(self,name,meta):
        self.namespace = getattr(meta,"namespace",None)
        self.namespace_prefix = getattr(meta,"namespace_prefix",None)
        self.tagname = getattr(meta,"tagname",name)


class BaseMetaclass(type):
    """Metaclass for dexml.Base and subclasses."""

    def __new__(mcls,name,bases,attrs):
        super_new = super(BaseMetaclass,mcls).__new__
        cls = super_new(mcls,name,bases,attrs)
        #  Don't do anything if it's not a subclass of Base
        parents = [b for b in bases if isinstance(b, BaseMetaclass)]
        if not parents:
            return cls
        cls._meta = Meta(name,attrs.get("meta"))
        cls._fields = []
        for (name,value) in attrs.iteritems():
            if isinstance(value,fields.Field):
                value.field_name = name
                value.field_class = cls
                cls._fields.append(value)
        cls._fields.sort(key=lambda f: f._order_counter)
        return cls


class Base(object):
    """Base class for dexml objects."""

    __metaclass__ = BaseMetaclass

    @classmethod
    def dexml(cls,xml):
        """Produce an instance of this object from some xml.

        The passed xml can be a string, a readble file-like object, or
        a DOM node; we might add support for more types in the future.
        """
        self = cls()
        node = self._make_xml_node(xml)
        self._validate_xml_node(node)
        children = CheckpointIter(node.childNodes)
        for f in self._fields:
            children.checkpoint()
            try:
                f.parse_node(self,node,children)
            except StopIteration:
                raise ParseError("Missing child nodes")
            except ParseError:
                if f.required:
                    raise
                children.revert()
        try:
            children.next()
            raise ParseError("Uncomsumed child nodes")
        except StopIteration:
            pass
        return self

    def rexml(self,encoding=None,fragment=False):
        """Produce xml from this object's instance data.

        A unicode string will be returned if any of the objects contain
        unicode values; specifying the 'encoding' argument forces generation
        of an ASCII string.

        By default a complete XML document is produced, including the
        leading "<?xml>" declaration.  To generate an XML fragment set
        the 'fragment' argument to True.
        """
        data = []
        if not fragment:
            if encoding:
                s = '<?xml version="1.0" encoding="%s" ?>' % (encoding,)
                data.append(s)
            else:
                data.append('<?xml version="1.0" ?>')
        data.extend(self._rexml())
        xml = "".join(data)
        if encoding:
            xml = xml.encode(encoding)
        return xml

    def _rexml(self):
        attrs = []
        children = []
        num = 0
        for f in self._fields:
            attrs.extend(f.render_attributes(self))
            children.extend(f.render_children(self))
            if len(attrs) + len(children) == num and f.required:
                raise RenderError("Field '%s' is missing" % (f.field_name,))
        if self._meta.namespace:
            if self._meta.namespace_prefix:
                tagname = "%s:%s" % (self._meta.namespace_prefix,self._meta.tagname)
                open_tag_contents = [tagname] + attrs
                open_tag_contents.append('xmlns:%s="%s"'%(self._meta.namespace_prefix,self._meta.namespace))
            else:
                open_tag_contents = [self._meta.tagname] + attrs
                open_tag_contents.append('xmlns="%s"'%(self._meta.namespace,))
        else:
            open_tag_contents = [self._meta.tagname] + attrs
        close_tag_contents = self._meta.tagname
        if children:
            yield "<%s>" % (" ".join(open_tag_contents),)
            for chld in children:
                yield chld
            yield "</%s>" % (close_tag_contents,)
        else:
            yield "<%s />" % (" ".join(open_tag_contents),)

    def _make_xml_node(self,xml):
        """Transform a variety of input formats to an XML DOM node."""
        try:
            ntype = xml.nodeType
        except AttributeError:
            if isinstance(xml,basestring):
                xml = minidom.parseString(xml)
            elif hasattr(xml,"read"):
                xml = minidom.parse(xml)
            else:
                raise ValueError("Can't convert that to an XML DOM node")
            node = xml.documentElement
        else:
            if ntype == xml.DOCUMENT_NODE:
                node = xml.documentElement
            else:
                node = xml
        return node

    def _validate_xml_node(self,node):
        """Check that the given xml node is valid for this object.

        Here 'valid' means that it is the right tag, in the right
        namespace.  We might add more eventually...
        """
        if node.nodeType != node.ELEMENT_NODE:
            err = "Class '%s' got a non-element node"
            err = err % (self.__class__.__name__,)
            raise ParseError(err)
        if node.localName != self._meta.tagname:
            err = "Class '%s' got tag '%s' (expected '%s')"
            err = err % (self.__class__.__name__,node.localName,
                         self._meta.tagname)
            raise ParseError(err)
        if self._meta.namespace:
            if node.namespaceURI != self._meta.namespace:
                err = "Class '%s' got namespace '%s' (expected '%s')"
                err = err % (self.__class__.__name__,node.namespaceURI,
                             self._meta.namespace)
                raise ParseError(err)
        else:
            if node.namespaceURI:
                err = "Class '%s' got namespace '%s' (expected no namespace)"
                err = err % (self.__class__.__name__,node.namespaceURI,)
                raise ParseError(err)


class CheckpointIter:
    """Iterator with checkpointing capabilities."""

    def __init__(self,seq):
        self._seq = iter(seq)
        self._tail = []
        self._head = []

    def checkpoint(self):
        self._tail = []

    def revert(self):
        self._head = self._tail + self._head
        self._tail = []

    def next(self):
        if self._head:
            item = self._head.pop(0)
        else:
            item = self._seq.next()
        self._tail.append(item)
        return item
 
