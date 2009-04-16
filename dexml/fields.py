
import dexml

_order_counter = 0

class Field(object):
    """Base class for all dexml Field classes."""

    class arguments:
        required = True

    def __init__(self,**kwds):
        global _order_counter
        args = self.__class__.arguments
        for argnm in dir(args):
            if not argnm.startswith("__"):
                setattr(self,argnm,kwds.get(argnm,getattr(args,argnm)))
        self._order_counter = _order_counter = _order_counter + 1

    def parse_node(self,obj,node,children):
        raise NotImplementedError

    def render_attributes(self,obj):
        raise NotImplementedError

    def render_children(self,obj):
        raise NotImplementedError

    def __get__(self,instance,owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.field_name)

    def __set__(self,instance,value):
        instance.__dict__[self.field_name] = value

    def _check_tagname(self,node,tagname):
        if node.nodeType != node.ELEMENT_NODE:
            raise dexml.ParseError("Not an element node")
        if isinstance(tagname,basestring):
            if node.localName != tagname:
                raise dexml.ParseError("tag doesn't match")
            if node.namespaceURI:
                if node.namespaceURI != self.field_class._meta.namespace:
                    raise dexml.ParseError("namespace doesn't match")
        else:
            (tagns,tagname) = tagname
            if node.localName != tagname:
                raise dexml.ParseError("tag doesn't match")
            if node.namespaceURI != tagns:
                raise dexml.ParseError("namespace doesn't match")

    def _get_attribute(self,node,attr):
        if isinstance(attr,basestring):
            if not node.hasAttribute(attr):
                raise dexml.ParseError("no such attribute: '%s'" % (attr,))
            return node.getAttribute(attr)
        else:
            (ns,attr) = attr
            if not node.hasAttributeNS(attr,ns):
                raise dexml.ParseError("no such attribute: '%s'" % (attr,))
            return node.getAttributeNS(attr,ns)
            

class Value(Field):

    class arguments(Field.arguments):
        tagname = None
        attrname = None
        default = None

    def __init__(self,**kwds):
        super(Value,self).__init__(**kwds)
        if self.default is not None:
            self.required = False

    def _get_attrname(self):
        return self.__dict__.get('attrname',self.field_name)
    def _set_attrname(self,attrname):
        if attrname is None:
            self.__dict__.pop('attrname',None)
        else:
            self.__dict__['attrname'] = attrname
    attrname = property(_get_attrname,_set_attrname)

    def __get__(self,instance,owner=None):
        val = super(Value,self).__get__(instance,owner)
        if val is None:
            return self.default
        return val

    def parse_node(self,obj,node,children):
        if self.tagname:
            chld = children.next()
            self._check_tagname(chld,self.tagname)
            vals = []
            for chld2 in chld.childNodes:
                if chld2.nodeType != chld2.TEXT_NODE:
                    raise dexml.ParseError("non-text value node")
                vals.append(chld2.nodeValue)
            val = "".join(vals)
        else:
            val = self._get_attribute(node,self.attrname)
        self.__set__(obj,self.parse_value(val))

    def render_attributes(self,obj):
        val = self.__get__(obj)
        if val is not None and val is not self.default and not self.tagname:
            yield '%s="%s"' % (self.attrname,self.render_value(val),)

    def render_children(self,obj):
        val = self.__get__(obj)
        if val is not None and val is not self.default and self.tagname:
            val = self.render_value(val)
            yield "<%s>%s</%s>" % (self.tagname,val,self.tagname)

    def parse_value(self,val):
        raise NotImplementedError

    def render_value(self,val):
        return str(val)


class String(Value):
    def parse_value(self,val):
        return val


class Integer(Value):
    def parse_value(self,val):
        return int(val)


class Float(Value):
    def parse_value(self,val):
        return float(val)

