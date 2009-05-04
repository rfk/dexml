
import dexml

_order_counter = 0

class _AttrBucket:
    """A simple class used only to hold attributes."""
    pass


class Field(object):
    """Base class for all dexml Field classes.

    Field classes are responsiblef or parsing and rendering individual
    components to the XML.  They also act as descriptors on dexml class
    instances, to get/set the corresponding properties.
    """

    class arguments:
        required = True

    def __init__(self,**kwds):
        global _order_counter
        args = self.__class__.arguments
        for argnm in dir(args):
            if not argnm.startswith("__"):
                setattr(self,argnm,kwds.get(argnm,getattr(args,argnm)))
        self._order_counter = _order_counter = _order_counter + 1

    def parse_attributes(self,obj,attrs):
        """Parse any attributes for this field form the given list.

        A list of the unconsumed attributes should be returned.
        """
        return attrs

    def parse_child_node(self,obj,node):
        """Parse data from the given child node.

        If the node is properly passed and no more data will be accepted,
        return dexml.PARSE_DONE.  If the node is properly parsed and more
        child nodes can be accepted, retrn dexml.PARSE_MORE.  Any other
        return value will be taken as a parsing error.
        """
        return dexml.PARSE_SKIP

    def parse_done(self,obj):
        """Finalize parsing for the given object."""
        pass

    def render_attributes(self,obj,val):
        """Render any attributes that this field manages."""
        return []

    def render_children(self,obj,nsmap,val):
        """Render any child nodes that this field manages."""
        return []

    def __get__(self,instance,owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.field_name)

    def __set__(self,instance,value):
        instance.__dict__[self.field_name] = value

    def _check_tagname(self,node,tagname):
        if node.nodeType != node.ELEMENT_NODE:
            return False
        if isinstance(tagname,basestring):
            if node.localName != tagname:
                return False
            if node.namespaceURI:
                if node.namespaceURI != self.field_class._meta.namespace:
                    return False
        else:
            (tagns,tagname) = tagname
            if node.localName != tagname:
                return False
            if node.namespaceURI != tagns:
                return False
        return True

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

    def parse_attributes(self,obj,attrs):
        if not self.tagname:
            unused = []
            attrname = self.attrname
            if isinstance(attrname,basestring):
                ns = None
            else:
                (ns,attrname) = attrname
            for attr in attrs:
                if attr.localName == attrname:
                    if ns is None or attr.namespaceURI == ns:
                        self.__set__(obj,self.parse_value(attr.nodeValue))
                    else:
                        unused.append(attr)
                else:
                    unused.append(attr)
            return unused
        else:
            return attrs

    def parse_child_node(self,obj,node):
        if self.tagname:
            if not self._check_tagname(node,self.tagname):
                return dexml.PARSE_SKIP
            vals = []
            for child in node.childNodes:
                if child.nodeType != child.TEXT_NODE:
                    raise dexml.ParseError("non-text value node")
                vals.append(child.nodeValue)
            self.__set__(obj,self.parse_value("".join(vals)))
            return dexml.PARSE_DONE
        else:
            return dexml.PARSE_SKIP
        return self.parse_value(val)

    def render_attributes(self,obj,val):
        if val is not None and val is not self.default and not self.tagname:
            yield '%s="%s"' % (self.attrname,self.render_value(val),)

    def render_children(self,obj,val,nsmap):
        if val is not None and val is not self.default and self.tagname:
            val = self.render_value(val)
            if isinstance(self.tagname,basestring):
                prefix = self.field_class._meta.namespace_prefix
                if prefix:
                    yield "<%s:%s>%s</%s:%s>" % (prefix,self.tagname,val,prefix,self.tagname)
                else:
                    yield "<%s>%s</%s>" % (self.tagname,val,self.tagname)
        # TODO: support (ns,tagname) form

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
        return self.__dict__.get("type")
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

    def parse_child_node(self,obj,node):
        typeclass = self.typeclass
        if typeclass is None:
            err = "Unknown typeclass '%s' for field '%s'"
            err = err % (self.type,self.field_name)
            raise dexml.ParseError(err)
        try:
            typeclass.validate_xml_node(node)
        except dexml.ParseError:
            return dexml.PARSE_SKIP
        else:
            inst = typeclass.parse(node)
            self.__set__(obj,inst)
            return dexml.PARSE_DONE

    def render_attributes(self,obj,val):
        return []

    def render_children(self,obj,val,nsmap):
        if val is not None:
            yield val.render(fragment=True,nsmap=nsmap)


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
        if not self.minlength:
            self.required = False

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

    def parse_child_node(self,obj,node):
        tmpobj = _AttrBucket()
        res = self.field.parse_child_node(tmpobj,node)
        if res is dexml.PARSE_MORE:
            raise RuntimeError("items in a list cannot return PARSE_MORE")
        if res is dexml.PARSE_DONE:
            items = self.__get__(obj)
            val = getattr(tmpobj,self.field_name)
            items.append(val)
            return dexml.PARSE_MORE
        else:
            return dexml.PARSE_SKIP

    def parse_done(self,obj):
        items = self.__get__(obj)
        if self.minlength is not None and len(items) < self.minlength:
            raise dexml.ParseError("Field '%s': not enough items" % (self.field_name,))
        if self.maxlength is not None and len(items) > self.maxlength:
            raise dexml.ParseError("Field '%s': too many items" % (self.field_name,))

    def render_children(self,obj,items,nsmap):
        if self.minlength is not None and len(items) < self.minlength:
            if self.required:
                raise dexml.RenderError("Field '%s': not enough items" % (self.field_name,))
        if self.maxlength is not None and len(items) > self.maxlength:
            raise dexml.RenderError("too many items")
        for item in items:
            for data in self.field.render_children(obj,item,nsmap):
                yield data


class Choice(Field):
    """Accept any one of a given set of Item fields."""

    class arguments(Field.arguments):
        fields = []

    def __init__(self,*fields,**kwds):
        real_fields = []
        for field in fields:
            if isinstance(field,Item):
                real_fields.append(field)
            elif isinstance(field,basestring):
                real_fields.append(Item(field))
            else:
                raise dexml.Error("only Item fields are allowed within a Choice field")
        kwds["fields"] = real_fields
        super(Choice,self).__init__(**kwds)

    def parse_child_node(self,obj,node):
        for field in self.fields:
            field.field_name = self.field_name
            res = field.parse_child_node(obj,node)
            if res is dexml.PARSE_MORE:
                raise RuntimeError("items in a Choice cannot return PARSE_MORE")
            if res is dexml.PARSE_DONE:
                return dexml.PARSE_DONE
        else:
            return dexml.PARSE_SKIP

    def render_children(self,obj,item,nsmap):
        yield item.render(fragment=True,nsmap=nsmap)


class XmlNode(Field):

    class arguments(Field.arguments):
        tagname = None

    def __set__(self,instance,value):
        if isinstance(value,basestring):
            doc = dexml.minidom.parseString(value)
            value = doc.documentElement
        return super(XmlNode,self).__set__(instance,value)

    def parse_child_node(self,obj,node):
        if self.tagname is None or node.localName == self.tagname:
            self.__set__(obj,node)
            return dexml.PARSE_DONE
        return dexml.PARSE_SKIP

    def render_children(self,obj,val,nsmap):
        yield val.toxml()

