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

    instances = {}

    def __new__(mcls,name,bases,attrs):
        super_new = super(BaseMetaclass,mcls).__new__
        cls = super_new(mcls,name,bases,attrs)
        #  Don't do anything if it's not a subclass of Base
        parents = [b for b in bases if isinstance(b, BaseMetaclass)]
        if not parents:
            return cls
        #  Set up the _meta object, inheriting from base classes
        cls._meta = Meta(name,attrs.get("meta"))
        for base in bases:
            if not isinstance(b,BaseMetaclass):
                continue
            if not hasattr(b,"_meta"):
                continue
            for attr in dir(base._meta):
                if attr.startswith("__"):
                    continue
                if getattr(cls._meta,attr) is None:
                    val = getattr(base._meta,attr)
                    if val is not None:
                        setattr(cls._meta,attr,val)
                
        #  Create ordered list of field objects, telling each about their
        #  name and containing class.
        cls._fields = []
        for (name,value) in attrs.iteritems():
            if isinstance(value,fields.Field):
                value.field_name = name
                value.field_class = cls
                cls._fields.append(value)
        cls._fields.sort(key=lambda f: f._order_counter)
        #  Register the new class so we can find it by name later on
        mcls.instances[(cls._meta.namespace,cls._meta.tagname)] = cls
        return cls

    @classmethod
    def find_class(mcls,tagname,namespace=None):
        return mcls.instances.get((namespace,tagname))


class Base(object):
    """Base class for dexml objects."""

    __metaclass__ = BaseMetaclass

    def __init__(self,**kwds):
        for f in self._fields:
            val = kwds.get(f.field_name)
            setattr(self,f.field_name,val)

    @classmethod
    def parse(cls,xml):
        """Produce an instance of this object from some xml.

        The passed xml can be a string, a readble file-like object, or
        a DOM node; we might add support for more types in the future.
        """
        self = cls()
        node = self._make_xml_node(xml)
        self._validate_xml_node(node)
        children = CheckpointIter(FilterNodes(node.childNodes))
        for f in self._fields:
            children.checkpoint()
            try:
                val = f.parse_node(node,children)
            except StopIteration:
                if f.required:
                    raise ParseError("Missing child nodes")
            except ParseError:
                if f.required:
                    raise
                children.revert()
            else:
                children.commit()
                setattr(self,f.field_name,val)
        try:
            children.next()
            raise ParseError("Uncomsumed child nodes")
        except StopIteration:
            pass
        return self

    def render(self,encoding=None,fragment=False,nsmap=None):
        """Produce xml from this object's instance data.

        A unicode string will be returned if any of the objects contain
        unicode values; specifying the 'encoding' argument forces generation
        of an ASCII string.

        By default a complete XML document is produced, including the
        leading "<?xml>" declaration.  To generate an XML fragment set
        the 'fragment' argument to True.
        """
        if nsmap is None:
            nsmap = {}
        data = []
        if not fragment:
            if encoding:
                s = '<?xml version="1.0" encoding="%s" ?>' % (encoding,)
                data.append(s)
            else:
                data.append('<?xml version="1.0" ?>')
        data.extend(self._render(nsmap))
        xml = "".join(data)
        if encoding:
            xml = xml.encode(encoding)
        return xml

    def _render(self,nsmap):
        #  Determine opening and closing tags
        pushed_ns = False
        if self._meta.namespace:
            namespace = self._meta.namespace
            prefix = self._meta.namespace_prefix
            try:
                cur_ns = nsmap[prefix]
            except KeyError:
                cur_ns = []
                nsmap[prefix] = cur_ns
            if prefix:
                tagname = "%s:%s" % (prefix,self._meta.tagname)
                open_tag_contents = [tagname]
                if not cur_ns or cur_ns[0] != namespace:
                    cur_ns.insert(0,namespace)
                    pushed_ns = True
                    open_tag_contents.append('xmlns:%s="%s"'%(prefix,namespace))
                close_tag_contents = tagname
            else:
                open_tag_contents = [self._meta.tagname]
                if not cur_ns or cur_ns[0] != namespace:
                    cur_ns.insert(0,namespace)
                    pushed_ns = True
                    open_tag_contents.append('xmlns="%s"'%(namespace,))
                close_tag_contents = self._meta.tagname
        else:
            open_tag_contents = [self._meta.tagname] 
            close_tag_contents = self._meta.tagname
        # Find the attributes and child nodes
        attrs = []
        children = []
        num = 0
        for f in self._fields:
            val = getattr(self,f.field_name)
            attrs.extend(f.render_attributes(self,val))
            children.extend(f.render_children(self,val,nsmap))
            if len(attrs) + len(children) == num and f.required:
                raise RenderError("Field '%s' is missing" % (f.field_name,))
        #  Actually construct the XML
        if pushed_ns:
            nsmap[prefix].pop(0)
        open_tag_contents.extend(attrs)
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
                try:
                    xml = minidom.parseString(xml)
                except Exception, e:
                    raise XmlError(e)
            elif hasattr(xml,"read"):
                try:
                    xml = minidom.parse(xml)
                except Exception, e:
                    raise XmlError(e)
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
        self._head = []
        self._tails = []

    def checkpoint(self):
        self._tails.append([])

    def commit(self):
        if not self._tails:
            raise RuntimeError("no checkpoint to commit")
        self._tails.pop()

    def revert(self):
        if not self._tails:
            raise RuntimeError("no checkpoint to revert")
        items = self._tails.pop()
        self._head = items + self._head

    def next(self):
        if self._head:
            item = self._head.pop()
        else:
            item = self._seq.next()
        if self._tails:
            self._tails[-1].append(item)
        return item

    def __iter__(self):
        return self


def FilterNodes(nodes):
    for node in nodes:
        if node.nodeType == node.ELEMENT_NODE:
            yield node
        elif node.nodeType == node.TEXT_NODE:
            if node.nodeValue.strip():
                yield node
 
