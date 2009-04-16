
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

    def render_children(self,obj,nsmap):
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
                raise dexml.ParseError("tag doesn't match: '%s'" % (node.localName,))
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

    def parse_node(self,node,children):
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
        return self.parse_value(val)

    def render_attributes(self,obj,val):
        if val is not None and val is not self.default and not self.tagname:
            yield '%s="%s"' % (self.attrname,self.render_value(val),)

    def render_children(self,obj,val,nsmap):
        if val is not None and val is not self.default and self.tagname:
            val = self.render_value(val)
            yield "<%s>%s</%s>" % (self.tagname,val,self.tagname)

    def parse_value(self,val):
        return val

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


class Boolean(Value):

    def __init__(self,**kwds):
        super(Boolean,self).__init__(**kwds)
        if self.tagname is not None:
            self.required = False
            self.default = False

    def parse_value(self,val):
        if val.lower() in ("no","off","false","0"):
            return False
        return True


class Item(Field):

    class arguments(Field.arguments):
        type = None

    def __init__(self,type=None,**kwds):
        kwds["type"] = type
        super(Item,self).__init__(**kwds)

    def _get_type(self):
        return self.__dict__.get("type",self.field_name)
    def _set_type(self,value):
        if value is not None:
            self.__dict__["type"] = value
    type = property(_get_type,_set_type)

    @property
    def typeclass(self):
        try:
            return self.__dict__['typeclass']
        except KeyError:
            self.__dict__['typeclass'] = self._load_typeclass()
            return self.__dict__['typeclass']
 
    def _load_typeclass(self):
        typ = self.type
        if isinstance(typ,dexml.BaseMetaclass):
            return typ
        if typ is None:
            typ = self.field_name
        typeclass = None
        if isinstance(typ,basestring):
            if self.field_class._meta.namespace:
                ns = self.field_class._meta.namespace
                typeclass = dexml.BaseMetaclass.find_class(typ,ns)
            if typeclass is None:
                typeclass = dexml.BaseMetaclass.find_class(typ,None)
        else:
            (ns,typ) = typ
            if isinstance(typ,dexml.BaseMetaclass):
                return typ
            if isinstance(ns,basestring):
                typeclass = dexml.BaseMetaclass.find_class(typ,ns)
                if typeclass is None and ns is None:
                    ns = self.field_class._meta.namespace
                    typeclass = dexml.BaseMetaclass.find_class(typ,ns)
            else:
                typeclass = ns[typ]
        return typeclass

    def parse_node(self,node,children):
        typeclass = self.typeclass
        if typeclass is None:
            err = "Unknown typeclass '%s' for field '%s'"
            err = err % (self.type,self.field_name)
            raise dexml.ParseError(err)
        child = children.next()
        return typeclass.dexml(child)

    def render_attributes(self,obj,val):
        return []

    def render_children(self,obj,val,nsmap):
        if val is not None:
            yield val.rexml(fragment=True,nsmap=nsmap)


class List(Field):

    class arguments(Field.arguments):
        field = None
        minlength = None
        maxlength = None

    def __init__(self,field,**kwds):
        if isinstance(field,Field):
            kwds["field"] = field
        else:
            kwds["field"] = Item(field,**kwds)
        super(List,self).__init__(**kwds)

    def _get_field(self):
        field = self.__dict__["field"]
        if not hasattr(field,"field_name"):
            field.field_name = self.field_name
        if not hasattr(field,"field_class"):
            field.field_class = self.field_class
        return field
    def _set_field(self,field):
        self.__dict__["field"] = field
    field = property(_get_field,_set_field)

    def __get__(self,instance,owner=None):
        val = super(List,self).__get__(instance,owner)
        if val is not None:
            return val
        self.__set__(instance,[])
        return self.__get__(instance,owner)

    def parse_node(self,node,children):
        items = []
        while True:
            children.checkpoint()
            try:
                val = self.field.parse_node(node,children)
            except dexml.ParseError, e:
                children.revert()
                break
            except StopIteration:
                break
            children.commit()
            items.append(val)
        if self.minlength is not None and len(items) < self.minlength:
            children.checkpoint()
            chld = children.next()
            children.revert()
            raise dexml.ParseError("Field '%s': not enough items" % (self.field_name,))
        if self.maxlength is not None and len(items) > self.maxlength:
            raise dexml.ParseError("too many items")
        return items

    def render_attributes(self,obj,val):
        return []

    def render_children(self,obj,items,nsmap):
        if self.minlength is not None and len(items) < self.minlength:
            if self.required:
                raise dexml.ParseError("Field '%s': not enough items" % (self.field_name,))
        if self.maxlength is not None and len(items) > self.maxlength:
            raise dexml.RenderError("too many items")
        for item in items:
            for data in self.field.render_children(obj,item,nsmap):
                yield data


class XmlNode(Field):

    class arguments(Field.arguments):
        tagname = None

    def parse_node(self,node,children):
        child = children.next()
        if self.tagname is None or child.localName == self.tagname:
            return child
        raise dexml.ParseError("tag doesn't match XmlNode")

    def render_attributes(self,obj,val):
        return []

    def render_children(self,obj,val,nsmap):
        yield val.toxml()

