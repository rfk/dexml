"""

  dexml.fields:  basic field type definitions for dexml

"""

import dexml

#  Global counter tracking the order in which fields are declared.
_order_counter = 0

class _AttrBucket:
    """A simple class used only to hold attributes."""
    pass


class Field(object):
    """Base class for all dexml Field classes.

    Field classes are responsible for parsing and rendering individual
    components to the XML.  They also act as descriptors on dexml Model
    instances, to get/set the corresponding properties.

    Each field instance will magically be given the following properties:

      * model_class:  the Model subclass to which it is attached
      * field_name:   the name under which is appears on that class

    The following methods are required for interaction with the parsing
    and rendering machinery:

      * parse_attributes:    parse info out of XML node attributes
      * parse_child_node:    parse into out of an XML child node
      * render_attributes:   render XML for node attributes
      * render_children:     render XML for child nodes
      
    """

    class arguments:
        required = True

    def __init__(self,**kwds):
        """Default Field constructor.

        This constructor keeps track of the order in which Field instances
        are created, since this information can have semantic meaning in
        XML.  It also merges any keyword arguments with the defaults
        defined on the 'arguments' inner class, and assigned these attributes
        to the Field instance.
        """
        global _order_counter
        self._order_counter = _order_counter = _order_counter + 1
        args = self.__class__.arguments
        for argnm in dir(args):
            if not argnm.startswith("__"):
                setattr(self,argnm,kwds.get(argnm,getattr(args,argnm)))

    def parse_attributes(self,obj,attrs):
        """Parse any attributes for this field from the given list.

        This method will be called with the Model instance being parsed and
        a list of attribute nodes from its XML tag.  Any attributes of 
        interest to this field should be processed, and a list of the unused
        attribute nodes returned.
        """
        return attrs

    def parse_child_node(self,obj,node):
        """Parse a child node for this field.

        This method will be called with the Model instance being parsed and
        the current child node of that model's XML tag.  There are three
        options for processing this node:

            * return PARSE_DONE, indicating that it was consumed and this
              field now has all the necessary data.
            * return PARSE_MORE, indicating that it was consumed but this
              field will accept more nodes.
            * return PARSE_SKIP, indicating that it was not consumed by
              this field.

        Any other return value will be taken as a parse error.
        """
        return dexml.PARSE_SKIP

    def parse_done(self,obj):
        """Finalize parsing for the given object.

        This method is called as a simple indicator that no more data will
        be forthcoming.  No return value is expected.
        """
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
                if node.namespaceURI != self.model_class.meta.namespace:
                    return False
        else:
            (tagns,tagname) = tagname
            if node.localName != tagname:
                return False
            if node.namespaceURI != tagns:
                return False
        return True


class Value(Field):
    """Field subclass that holds a simple scalar value.

    This Field subclass contains the common logic to parse/render simple
    scalar value fields - fields that don't required any recursive parsing.
    Individual subclasses should provide the parse_value() and render_value()
    methods to do type coercion of the value.

    Value fields can also have a default value, specified by the 'default'
    keyword argument.

    By default, the field maps to an attribute of the model's XML node with
    the same name as the field declaration.  Consider:

        class MyModel(Model):
            my_field = fields.Value(default="test")


    This corresponds to the XML fragment "<MyModel my_field='test' />".
    To use a different name specify the 'attrname' kwd argument.  To use
    a subtag instead of an attribute specify the 'tagname' kwd argument.

    Namespaced attributes or subtags are also supported, by specifying a
    (namespace,tagname) pair for 'attrname' or 'tagname' respectively.
    """

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
        #  Bail out if we're attached to a subtag rather than an attr.
        if self.tagname:
            return attrs
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

    def parse_child_node(self,obj,node):
        if not self.tagname:
            return dexml.PARSE_SKIP
        if not self._check_tagname(node,self.tagname):
            return dexml.PARSE_SKIP
        vals = []
        #  Merge all text nodes into a single value
        for child in node.childNodes:
            if child.nodeType != child.TEXT_NODE:
                raise dexml.ParseError("non-text value node")
            vals.append(child.nodeValue)
        self.__set__(obj,self.parse_value("".join(vals)))
        return dexml.PARSE_DONE

    def render_attributes(self,obj,val):
        if val is not None and val is not self.default and not self.tagname:
            yield '%s="%s"' % (self.attrname,self.render_value(val),)
        # TODO: support (ns,attrname) form

    def render_children(self,obj,val,nsmap):
        if val is not None and val is not self.default and self.tagname:
            val = self.render_value(val)
            if isinstance(self.tagname,basestring):
                prefix = self.model_class.meta.namespace_prefix
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
    """Field representing a simple string value."""
    # actually, the base Value() class will do this automatically.
    pass


class Integer(Value):
    """Field representing a simple integer value."""
    def parse_value(self,val):
        return int(val)


class Float(Value):
    """Field representing a simple float value."""
    def parse_value(self,val):
        return float(val)


class Boolean(Value):
    """Field representing a simple boolean value.

    The strings corresponding to false are 'no', 'off', 'false' and '0',
    compared case-insensitively.
    """

    def __init__(self,**kwds):
        super(Boolean,self).__init__(**kwds)

    def parse_value(self,val):
        if val.lower() in ("no","off","false","0"):
            return False
        return True


class Model(Field):
    """Field subclass referencing another Model instance.

    This field sublcass allows Models to contain other Models recursively.
    The first argument to the field constructor must be either a Model
    class or the name of a Model class.
    """

    class arguments(Field.arguments):
        type = None

    def __init__(self,type=None,**kwds):
        kwds["type"] = type
        super(Model,self).__init__(**kwds)

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
        if isinstance(typ,dexml.ModelMetaclass):
            return typ
        if typ is None:
            typ = self.field_name
        typeclass = None
        if isinstance(typ,basestring):
            if self.model_class.meta.namespace:
                ns = self.model_class.meta.namespace
                typeclass = dexml.ModelMetaclass.find_class(typ,ns)
            if typeclass is None:
                typeclass = dexml.ModelMetaclass.find_class(typ,None)
        else:
            (ns,typ) = typ
            if isinstance(typ,dexml.ModelMetaclass):
                return typ
            if isinstance(ns,basestring):
                typeclass = dexml.ModelMetaclass.find_class(typ,ns)
                if typeclass is None and ns is None:
                    ns = self.model_class.meta.namespace
                    typeclass = dexml.ModelMetaclass.find_class(typ,ns)
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
    """Field subclass representing a list of fields.

    This field corresponds to a homogenous list of other fields.  You would
    declare it like so:

      class MyModel(Model):
          items = fields.List(fields.String(tagname="item"))

    Corresponding to XML such as:

      <MyModel><item>one</item><item>two</item></MyModel>


    The properties 'minlength' and 'maxlength' control the allowable length
    of the list.
    """

    class arguments(Field.arguments):
        field = None
        minlength = None
        maxlength = None

    def __init__(self,field,**kwds):
        if isinstance(field,Field):
            kwds["field"] = field
        else:
            kwds["field"] = Model(field,**kwds)
        super(List,self).__init__(**kwds)
        if not self.minlength:
            self.required = False

    def _get_field(self):
        field = self.__dict__["field"]
        if not hasattr(field,"field_name"):
            field.field_name = self.field_name
        if not hasattr(field,"model_class"):
            field.model_class = self.model_class
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
            if self.required or len(items) != 0:
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
    """Field subclass accepting any one of a given set of Model fields."""

    class arguments(Field.arguments):
        fields = []

    def __init__(self,*fields,**kwds):
        real_fields = []
        for field in fields:
            if isinstance(field,Model):
                real_fields.append(field)
            elif isinstance(field,basestring):
                real_fields.append(Model(field))
            else:
                raise dexml.Error("only Model fields are allowed within a Choice field")
        kwds["fields"] = real_fields
        super(Choice,self).__init__(**kwds)

    def parse_child_node(self,obj,node):
        for field in self.fields:
            field.field_name = self.field_name
            field.model_class = self.model_class
            res = field.parse_child_node(obj,node)
            if res is dexml.PARSE_MORE:
                raise RuntimeError("items in a Choice cannot return PARSE_MORE")
            if res is dexml.PARSE_DONE:
                return dexml.PARSE_DONE
        else:
            return dexml.PARSE_SKIP

    def render_children(self,obj,item,nsmap):
        if item is None:
            if self.required:
                raise dexml.RenderError("Field '%s': required field is missing" % (self.field_name,))
        else:
            yield item.render(fragment=True,nsmap=nsmap)


class XmlNode(Field):

    class arguments(Field.arguments):
        tagname = None
        encoding = None

    def __set__(self,instance,value):
        if isinstance(value,basestring):
            if isinstance(value,unicode) and self.encoding:
                value = value.encode(self.encoding)
            doc = dexml.minidom.parseString(value)
            value = doc.documentElement
        return super(XmlNode,self).__set__(instance,value)

    def parse_child_node(self,obj,node):
        if self.tagname is None or node.localName == self.tagname:
            self.__set__(obj,node)
            return dexml.PARSE_DONE
        return dexml.PARSE_SKIP

    def render_children(self,obj,val,nsmap):
        if val is not None:
            yield val.toxml()

