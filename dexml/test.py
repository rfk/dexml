"""

  dexml.test:  testcases for dexml module.

"""

import sys
import os
import os.path
import difflib
import unittest
import doctest
from xml.dom import minidom
from StringIO import StringIO

import dexml
from dexml import fields


def b(raw):
    """Compatability wrapper for b"string" syntax."""
    return raw.encode("ascii")


def model_fields_equal(m1,m2):
    """Check for equality by comparing model fields."""
    for nm in m1.__class__._fields:
        v1 = getattr(m1,nm.field_name)
        v2 = getattr(m2,nm.field_name)
        if isinstance(v1,dexml.Model):
            if not model_fields_equal(v1,v2):
                return False
        elif v1 != v2:
            return False
    return True
          


class TestDexmlDocstring(unittest.TestCase):

    def test_docstring(self):
        """Test dexml docstrings

        We don't do this on python3 because of the many small ways in
        which the output has changed in that version.
        """
        if sys.version_info < (3,):
            assert doctest.testmod(dexml)[0] == 0

    def test_readme_matches_docstring(self):
        """Ensure that the README is in sync with the docstring.

        This test should always pass; if the README is out of sync it just
        updates it with the contents of dexml.__doc__.
        """
        dirname = os.path.dirname
        readme = os.path.join(dirname(dirname(__file__)),"README.rst")
        if not os.path.isfile(readme):
            f = open(readme,"wb")
            f.write(dexml.__doc__.encode())
            f.close()
        else:
            f = open(readme,"rb")
            if f.read() != dexml.__doc__:
                f.close()
                f = open(readme,"wb")
                f.write(dexml.__doc__.encode())
                f.close()



class TestDexml(unittest.TestCase):


    def test_base(self):
        """Test operation of a dexml.Model class with no fields."""
        class hello(dexml.Model):
            pass

        h = hello.parse("<hello />")
        self.assertTrue(h)

        h = hello.parse("<hello>\n</hello>")
        self.assertTrue(h)

        h = hello.parse("<hello>world</hello>")
        self.assertTrue(h)

        d = minidom.parseString("<hello>world</hello>")
        h = hello.parse(d)
        self.assertTrue(h)

        self.assertRaises(dexml.ParseError,hello.parse,"<Hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<hllo />")
        self.assertRaises(dexml.ParseError,hello.parse,"<hello xmlns='T:' />")

        hello.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError,hello.parse,"<hello>world</hello>")
        hello.meta.ignore_unknown_elements = True

        h = hello()
        self.assertEquals(h.render(),'<?xml version="1.0" ?><hello />')
        self.assertEquals(h.render(fragment=True),"<hello />")
        self.assertEquals(h.render(encoding="utf8"),b('<?xml version="1.0" encoding="utf8" ?><hello />'))
        self.assertEquals(h.render(encoding="utf8",fragment=True),b("<hello />"))

        self.assertEquals(h.render(),"".join(h.irender()))
        self.assertEquals(h.render(fragment=True),"".join(h.irender(fragment=True)))
        self.assertEquals(h.render(encoding="utf8"),b("").join(h.irender(encoding="utf8")))
        self.assertEquals(h.render(encoding="utf8",fragment=True),b("").join(h.irender(encoding="utf8",fragment=True)))


    def test_errors_on_malformed_xml(self):
        class hello(dexml.Model):
            pass

        self.assertRaises(dexml.XmlError,hello.parse,b("<hello>"))
        self.assertRaises(dexml.XmlError,hello.parse,b("<hello></helo>"))
        self.assertRaises(dexml.XmlError,hello.parse,b(""))

        self.assertRaises(dexml.XmlError,hello.parse,u"")
        self.assertRaises(dexml.XmlError,hello.parse,u"<hello>")
        self.assertRaises(dexml.XmlError,hello.parse,u"<hello></helo>")

        self.assertRaises(dexml.XmlError,hello.parse,StringIO("<hello>"))
        self.assertRaises(dexml.XmlError,hello.parse,StringIO("<hello></helo>"))
        self.assertRaises(dexml.XmlError,hello.parse,StringIO(""))

        self.assertRaises(ValueError,hello.parse,None)
        self.assertRaises(ValueError,hello.parse,42)
        self.assertRaises(ValueError,hello.parse,staticmethod)


    def test_unicode_model_tagname(self):
        """Test a dexml.Model class with a unicode tag name."""
        class hello(dexml.Model):
            class meta:
                tagname = u"hel\N{GREEK SMALL LETTER LAMDA}o"

        h = hello.parse(u"<hel\N{GREEK SMALL LETTER LAMDA}o />")
        self.assertTrue(h)

        h = hello.parse(u"<hel\N{GREEK SMALL LETTER LAMDA}o>\n</hel\N{GREEK SMALL LETTER LAMDA}o>")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.parse,u"<hello />")
        self.assertRaises(dexml.ParseError,hello.parse,u"<Hello />")
        self.assertRaises(dexml.ParseError,hello.parse,u"<hllo />")
        self.assertRaises(dexml.ParseError,hello.parse,u"<Hel\N{GREEK SMALL LETTER LAMDA}o />")

        h = hello.parse(u"<hel\N{GREEK SMALL LETTER LAMDA}o>world</hel\N{GREEK SMALL LETTER LAMDA}o>")
        self.assertTrue(h)

        h = hello.parse(u"<?xml version='1.0' encoding='utf-8' ?><hel\N{GREEK SMALL LETTER LAMDA}o>world</hel\N{GREEK SMALL LETTER LAMDA}o>")
        h = hello.parse(u"<?xml version='1.0' encoding='utf-16' ?><hel\N{GREEK SMALL LETTER LAMDA}o>world</hel\N{GREEK SMALL LETTER LAMDA}o>")
        self.assertTrue(h)

        h = hello()
        self.assertEquals(h.render(),u'<?xml version="1.0" ?><hel\N{GREEK SMALL LETTER LAMDA}o />')
        self.assertEquals(h.render(fragment=True),u"<hel\N{GREEK SMALL LETTER LAMDA}o />")
        self.assertEquals(h.render(encoding="utf8"),u'<?xml version="1.0" encoding="utf8" ?><hel\N{GREEK SMALL LETTER LAMDA}o />'.encode("utf8"))
        self.assertEquals(h.render(encoding="utf8",fragment=True),u"<hel\N{GREEK SMALL LETTER LAMDA}o />".encode("utf8"))

        self.assertEquals(h.render(),"".join(h.irender()))
        self.assertEquals(h.render(fragment=True),"".join(h.irender(fragment=True)))
        self.assertEquals(h.render(encoding="utf8"),b("").join(h.irender(encoding="utf8")))
        self.assertEquals(h.render(encoding="utf8",fragment=True),b("").join(h.irender(encoding="utf8",fragment=True)))

    def test_unicode_string_field(self):
        """Test a dexml.Model class with a unicode string field."""
        class Person(dexml.Model):
            name = fields.String()

        p = Person.parse(u"<Person name='hel\N{GREEK SMALL LETTER LAMDA}o'/>")
        self.assertEquals(p.name, u"hel\N{GREEK SMALL LETTER LAMDA}o")

        p = Person()
        p.name = u"hel\N{GREEK SMALL LETTER LAMDA}o"
        self.assertEquals(p.render(encoding="utf8"), u'<?xml version="1.0" encoding="utf8" ?><Person name="hel\N{GREEK SMALL LETTER LAMDA}o" />'.encode("utf8"))

    def test_model_meta_attributes(self):
        class hello(dexml.Model):
            pass

        self.assertRaises(dexml.ParseError,hello.parse,"<Hello />")
        hello.meta.case_sensitive = False
        self.assertTrue(hello.parse("<Hello />"))
        self.assertRaises(dexml.ParseError,hello.parse,"<Helpo />")
        hello.meta.case_sensitive = True

        self.assertTrue(hello.parse("<hello>world</hello>"))
        hello.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError,hello.parse,"<hello>world</hello>")
        hello.meta.ignore_unknown_elements = True


    def test_namespace(self):
        """Test basic handling of namespaces."""
        class hello(dexml.Model):
            class meta:
                namespace = "http://hello.com/"
                ignore_unknown_elements = False

        h = hello.parse("<hello xmlns='http://hello.com/' />")
        self.assertTrue(h)

        h = hello.parse("<H:hello xmlns:H='http://hello.com/' />")
        self.assertTrue(h)

        self.assertRaises(dexml.ParseError,hello.parse,"<hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hllo xmlns:H='http://hello.com/' />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hello xmlns:H='http://hello.com/'>world</H:hello>")

        hello.meta.case_sensitive = False
        self.assertRaises(dexml.ParseError,hello.parse,"<Hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hllo xmlns:H='http://hello.com/' />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hello xmlns:H='http://Hello.com/' />")
        hello.parse("<H:HeLLo xmlns:H='http://hello.com/' />")
        hello.meta.case_sensitive = True

        h = hello()
        self.assertEquals(h.render(fragment=True),'<hello xmlns="http://hello.com/" />')

        hello.meta.namespace_prefix = "H"
        self.assertEquals(h.render(fragment=True),'<H:hello xmlns:H="http://hello.com/" />')



    def test_base_field(self):
        """Test operation of the base Field class (for coverage purposes)."""
        class tester(dexml.Model):
            value = fields.Field()
        assert isinstance(tester.value,fields.Field)
        #  This is a parse error because Field doesn't consume any nodes
        self.assertRaises(dexml.ParseError,tester.parse,"<tester value='42' />")
        self.assertRaises(dexml.ParseError,tester.parse,"<tester><value>42</value></tester>")
        #  Likewise, Field doesn't output any XML so it thinks value is missing
        self.assertRaises(dexml.RenderError,tester(value=None).render)


    def test_value_fields(self):
        """Test operation of basic value fields."""
        class hello(dexml.Model):
            recipient = fields.String()
            sentby = fields.String(attrname="sender")
            strength = fields.Integer(default=1)
            message = fields.String(tagname="msg")

        h = hello.parse("<hello recipient='ryan' sender='lozz' strength='7'><msg>hi there</msg></hello>")
        self.assertEquals(h.recipient,"ryan")
        self.assertEquals(h.sentby,"lozz")
        self.assertEquals(h.message,"hi there")
        self.assertEquals(h.strength,7)

        #  These are parse errors due to namespace mismatches
        self.assertRaises(dexml.ParseError,hello.parse,"<hello xmlns:N='N:' N:recipient='ryan' sender='lozz' strength='7'><msg>hi there</msg></hello>")
        self.assertRaises(dexml.ParseError,hello.parse,"<hello xmlns:N='N:' recipient='ryan' sender='lozz' strength='7'><N:msg>hi there</N:msg></hello>")

        #  These are parse errors due to subtags
        self.assertRaises(dexml.ParseError,hello.parse,"<hello recipient='ryan' sender='lozz' strength='7'><msg>hi <b>there</b></msg></hello>")


    def test_float_field(self):
        class F(dexml.Model):
            value = fields.Float()
        self.assertEquals(F.parse("<F value='4.2' />").value,4.2)


    def test_boolean_field(self):
        class F(dexml.Model):
            value = fields.Boolean()
        self.assertTrue(F.parse("<F value='' />").value)
        self.assertTrue(F.parse("<F value='on' />").value)
        self.assertTrue(F.parse("<F value='YeS' />").value)
        self.assertFalse(F.parse("<F value='off' />").value)
        self.assertFalse(F.parse("<F value='no' />").value)
        self.assertFalse(F.parse("<F value='FaLsE' />").value)

        f = F.parse("<F value='' />")
        assert model_fields_equal(F.parse(f.render()),f)
        f.value = "someotherthing"
        assert model_fields_equal(F.parse(f.render()),f)
        f.value = False
        assert model_fields_equal(F.parse(f.render()),f)


    def test_string_with_special_chars(self):
        class letter(dexml.Model):
            message = fields.String(tagname="msg")

        l = letter.parse("<letter><msg>hello &amp; goodbye</msg></letter>")
        self.assertEquals(l.message,"hello & goodbye")
        l = letter.parse("<letter><msg><![CDATA[hello & goodbye]]></msg></letter>")
        self.assertEquals(l.message,"hello & goodbye")

        l = letter(message="XML <tags> are fun!")
        self.assertEquals(l.render(fragment=True),'<letter><msg>XML &lt;tags&gt; are fun!</msg></letter>')

        class update(dexml.Model):
            status = fields.String(attrname="status")

        u = update(status="feeling <awesome>!")
        self.assertEquals(u.render(fragment=True),'<update status="feeling &lt;awesome&gt;!" />')


    def test_cdata_fields(self):
        try:
            class update(dexml.Model):
                status = fields.CDATA()
            assert False, "CDATA allowed itself to be created without tagname"
        except ValueError:
            pass
        class update(dexml.Model):
            status = fields.CDATA(tagname=True)
        u = update(status="feeling <awesome>!")
        self.assertEquals(u.render(fragment=True),'<update><status><![CDATA[feeling <awesome>!]]></status></update>')


    def test_model_field(self):
        """Test operation of fields.Model."""
        class person(dexml.Model):
            name = fields.String()
            age = fields.Integer()
        class pet(dexml.Model):
            name = fields.String()
            species = fields.String(required=False)
        class Vet(dexml.Model):
            class meta:
                tagname = "vet"
            name = fields.String()
        class pets(dexml.Model):
            person = fields.Model()
            pet1 = fields.Model("pet")
            pet2 = fields.Model(pet,required=False)
            pet3 = fields.Model((None,pet),required=False)
            vet = fields.Model((None,"Vet"),required=False)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.species,"dog")
        self.assertEquals(p.pet2,None)

        p = pets.parse("<pets>\n<person name='ryan' age='26'/>\n<pet name='riley' species='dog' />\n<pet name='fishy' species='fish' />\n</pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.name,"riley")
        self.assertEquals(p.pet2.species,"fish")

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><pet name='fishy' species='fish' /><pet name='meowth' species='cat' /><vet name='Nic' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.name,"riley")
        self.assertEquals(p.pet2.species,"fish")
        self.assertEquals(p.pet3.species,"cat")
        self.assertEquals(p.vet.name,"Nic")

        self.assertRaises(dexml.ParseError,pets.parse,"<pets><pet name='riley' species='fish' /></pets>")
        self.assertRaises(dexml.ParseError,pets.parse,"<pets><person name='riley' age='2' /></pets>")
        
        def assign(val):
            p.pet1 = val
        self.assertRaises(ValueError, assign, person(name = 'ryan', age = 26))
        self.assertEquals(p.pet1.name,"riley")
        assign(pet(name="spike"))
        self.assertEquals(p.pet1.name,"spike")

        p = pets()
        self.assertRaises(dexml.RenderError,p.render)
        p.person = person(name="lozz",age="25")
        p.pet1 = pet(name="riley")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /></pets>')
        self.assertEquals("".join(p.irender(fragment=True)),'<pets><person name="lozz" age="25" /><pet name="riley" /></pets>')
        p.pet2 = pet(name="guppy",species="fish")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /></pets>')
        self.assertEquals("".join(p.irender(fragment=True)),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /></pets>')


    def test_model_field_namespace(self):
        """Test operation of fields.Model with namespaces"""
        class petbase(dexml.Model):
            class meta:
                namespace = "http://www.pets.com/PetML"
                namespace_prefix = "P"
        class person(petbase):
            name = fields.String()
            age = fields.Integer()
            status = fields.String(tagname=("S:","status"),required=False)
        class pet(petbase):
            name = fields.String()
            species = fields.String(required=False)
        class pets(petbase):
            person = fields.Model()
            pet1 = fields.Model("pet")
            pet2 = fields.Model(pet,required=False)

        p = pets.parse("<pets xmlns='http://www.pets.com/PetML'><person name='ryan' age='26'/><pet name='riley' species='dog' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.species,"dog")
        self.assertEquals(p.pet2,None)

        p = pets.parse("<P:pets xmlns:P='http://www.pets.com/PetML'><P:person name='ryan' age='26'/><P:pet name='riley' species='dog' /><P:pet name='fishy' species='fish' /></P:pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.name,"riley")
        self.assertEquals(p.pet2.species,"fish")

        self.assertRaises(dexml.ParseError,pets.parse,"<pets><pet name='riley' species='fish' /></pets>")
        self.assertRaises(dexml.ParseError,pets.parse,"<pets><person name='riley' age='2' /></pets>")

        p = pets()
        self.assertRaises(dexml.RenderError,p.render)

        p.person = person(name="lozz",age="25")
        p.pet1 = pet(name="riley")
        self.assertEquals(p.render(fragment=True),'<P:pets xmlns:P="http://www.pets.com/PetML"><P:person name="lozz" age="25" /><P:pet name="riley" /></P:pets>')

        p.pet2 = pet(name="guppy",species="fish")
        self.assertEquals(p.render(fragment=True),'<P:pets xmlns:P="http://www.pets.com/PetML"><P:person name="lozz" age="25" /><P:pet name="riley" /><P:pet name="guppy" species="fish" /></P:pets>')

        p = person.parse('<P:person xmlns:P="http://www.pets.com/PetML" name="ryan" age="26"><status>awesome</status></P:person>')
        self.assertEquals(p.status,None)
        p = person.parse('<P:person xmlns:P="http://www.pets.com/PetML" name="ryan" age="26"><P:status>awesome</P:status></P:person>')
        self.assertEquals(p.status,None)
        p = person.parse('<P:person xmlns:P="http://www.pets.com/PetML" xmlns:S="S:" name="ryan" age="26"><S:sts>awesome</S:sts></P:person>')
        self.assertEquals(p.status,None)
        p = person.parse('<P:person xmlns:P="http://www.pets.com/PetML" xmlns:S="S:" name="ryan" age="26"><S:status>awesome</S:status></P:person>')
        self.assertEquals(p.status,"awesome")


    def test_list_field(self):
        """Test operation of fields.List"""
        class person(dexml.Model):
            name = fields.String()
            age = fields.Integer()
        class pet(dexml.Model):
            name = fields.String()
            species = fields.String(required=False)
        class reward(dexml.Model):
            date = fields.String()
        class pets(dexml.Model):
            person = fields.Model()
            pets = fields.List("pet",minlength=1)
            notes = fields.List(fields.String(tagname="note"),maxlength=2)
            rewards = fields.List("reward",tagname="rewards",required=False)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pets[0].species,"dog")
        self.assertEquals(len(p.pets),1)
        self.assertEquals(len(p.notes),0)

        p = pets.parse("<pets>\n\t<person name='ryan' age='26'/>\n\t<pet name='riley' species='dog' />\n\t<pet name='fishy' species='fish' />\n\t<note>noted</note></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pets[0].name,"riley")
        self.assertEquals(p.pets[1].species,"fish")
        self.assertEquals(p.notes[0],"noted")
        self.assertEquals(len(p.pets),2)
        self.assertEquals(len(p.notes),1)

        self.assertRaises(dexml.ParseError,pets.parse,"<pets><pet name='riley' species='fish' /></pets>")
        self.assertRaises(dexml.ParseError,pets.parse,"<pets><person name='ryan' age='26' /></pets>")
        self.assertRaises(dexml.ParseError,pets.parse,"<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><note>too</note><note>many</note><note>notes</note></pets>")

        p = pets()
        p.person = person(name="lozz",age="25")
        self.assertRaises(dexml.RenderError,p.render)

        p.pets.append(pet(name="riley"))
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /></pets>')

        p.pets.append(pet(name="guppy",species="fish"))
        p.notes.append("noted")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /><note>noted</note></pets>')

        p = pets()
        p.person = person(name="lozz",age="25")
        yielded_items = []
        def gen_pets():
            for p in (pet(name="riley"),pet(name="guppy",species="fish")):
                yielded_items.append(p)
                yield p
        p.pets = gen_pets()
        self.assertEquals(len(yielded_items),0)
        p.notes.append("noted")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /><note>noted</note></pets>')
        self.assertEquals(len(yielded_items),2)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><rewards><reward date='February 23, 2010'/><reward date='November 10, 2009'/></rewards></pets>")
        self.assertEquals(len(p.rewards), 2)
        self.assertEquals(p.rewards[1].date, 'November 10, 2009')
        self.assertEquals(p.render(fragment = True), '<pets><person name="ryan" age="26" /><pet name="riley" species="dog" /><rewards><reward date="February 23, 2010" /><reward date="November 10, 2009" /></rewards></pets>')

        pets.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError, pets.parse, "<pets><person name='ryan' age='26' /><pet name='riley' species='dog' /><reward date='February 23, 2010'/><reward date='November 10, 2009' /></pets>")

    def test_list_field_tagname(self):
        """Test List(tagname="items",required=True)."""
        class obj(dexml.Model):
            items = fields.List(fields.String(tagname="item"),tagname="items")
        o = obj(items=[])
        self.assertEquals(o.render(fragment=True), '<obj><items /></obj>')
        self.assertRaises(dexml.ParseError,obj.parse,'<obj />')
        o = obj.parse('<obj><items /></obj>')
        self.assertEquals(o.items,[])

    def test_list_field_sanity_checks(self):
        class GreedyField(fields.Field):
            def parse_child_node(self,obj,node):
                return dexml.PARSE_MORE
        class SaneList(dexml.Model):
            item = fields.List(GreedyField(tagname="item"))
        self.assertRaises(ValueError,SaneList.parse,"<SaneList><item /><item /></SaneList>")


    def test_list_field_max_min(self):
        try:
            class MyStuff(dexml.Model):
                items = fields.List(fields.String(tagname="item"),required=False,minlength=2)
            assert False, "List allowed creation with nonsensical args"
        except ValueError:
            pass

        class MyStuff(dexml.Model):
            items = fields.List(fields.String(tagname="item"),required=False)
        self.assertEquals(MyStuff.parse("<MyStuff />").items,[])

        MyStuff.items.maxlength = 1
        self.assertEquals(MyStuff.parse("<MyStuff><item /></MyStuff>").items,[""])
        self.assertRaises(dexml.ParseError,MyStuff.parse,"<MyStuff><item /><item /></MyStuff>")
        s = MyStuff()
        s.items = ["one","two"]
        self.assertRaises(dexml.RenderError,s.render)

        MyStuff.items.maxlength = None
        MyStuff.items.minlength = 2
        MyStuff.items.required = True
        self.assertEquals(MyStuff.parse("<MyStuff><item /><item /></MyStuff>").items,["",""])
        self.assertRaises(dexml.ParseError,MyStuff.parse,"<MyStuff><item /></MyStuff>")


    def test_dict_field(self):
        """Test operation of fields.Dict"""
        class item(dexml.Model):
            name = fields.String()
            attr = fields.String(tagname = 'attr')
        class obj(dexml.Model):
            items = fields.Dict('item', key = 'name')

        xml = '<obj><item name="item1"><attr>val1</attr></item><item name="item2"><attr>val2</attr></item></obj>'
        o = obj.parse(xml)
        self.assertEquals(len(o.items), 2)
        self.assertEquals(o.items['item1'].name, 'item1')
        self.assertEquals(o.items['item2'].attr, 'val2')
        del o.items['item2']
        self.assertEquals(o.render(fragment = True), '<obj><item name="item1"><attr>val1</attr></item></obj>')

        o.items['item3'] = item(attr = 'val3')
        self.assertEquals(o.items['item3'].attr, 'val3')
        def _setitem():
            o.items['item3'] = item(name = 'item2', attr = 'val3')
        self.assertRaises(ValueError, _setitem)

        class obj(dexml.Model):
            items = fields.Dict(fields.Model(item), key = 'name', unique = True)
        xml = '<obj><item name="item1"><attr>val1</attr></item><item name="item1"><attr>val2</attr></item></obj>'
        self.assertRaises(dexml.ParseError, obj.parse, xml)

        class obj(dexml.Model):
            items = fields.Dict('item', key = 'name', tagname = 'items')
        xml = '<obj> <ignoreme /> <items> <item name="item1"><attr>val1</attr></item> <item name="item2"><attr>val2</attr></item> </items> </obj>'

        o = obj.parse(xml)
        self.assertEquals(len(o.items), 2)
        self.assertEquals(o.items['item1'].name, 'item1')
        self.assertEquals(o.items['item2'].attr, 'val2')
        del o.items['item2']
        self.assertEquals(o.render(fragment = True), '<obj><items><item name="item1"><attr>val1</attr></item></items></obj>')

        # Test that wrapper tags are still required even for empty fields
        o = obj(items={})
        self.assertEquals(o.render(fragment=True), '<obj><items /></obj>')
        o = obj.parse('<obj><items /></obj>')
        self.assertEquals(o.items,{})
        self.assertRaises(dexml.ParseError,obj.parse,'<obj />')
        obj.items.required = False
        self.assertEquals(o.render(fragment=True), '<obj />')
        obj.items.required = True

        from collections import defaultdict
        class _dict(defaultdict):
            def __init__(self):
                super(_dict, self).__init__(item)

        class obj(dexml.Model):
            items = fields.Dict('item', key = 'name', dictclass = _dict)
        o = obj()
        self.assertEquals(o.items['item1'].name, 'item1')


    def test_dict_field_sanity_checks(self):
        class GreedyField(fields.Field):
            def parse_child_node(self,obj,node):
                return dexml.PARSE_MORE
        class SaneDict(dexml.Model):
            item = fields.Dict(GreedyField(tagname="item"),key="name")
        self.assertRaises(ValueError,SaneDict.parse,"<SaneDict><item /></SaneDict>")

        class item(dexml.Model):
            name = fields.String()
            value = fields.String()
        class MyStuff(dexml.Model):
            items = fields.Dict(item,key="wrongname")
        self.assertRaises(dexml.ParseError,MyStuff.parse,"<MyStuff><ignoreme /><item name='hi' value='world' /></MyStuff>")


    def test_dict_field_max_min(self):
        class item(dexml.Model):
            name = fields.String()
            value = fields.String()
        try:
            class MyStuff(dexml.Model):
                items = fields.Dict(item,key="name",required=False,minlength=2)
            assert False, "Dict allowed creation with nonsensical args"
        except ValueError:
            pass

        class MyStuff(dexml.Model):
            items = fields.Dict(item,key="name",required=False)
        self.assertEquals(MyStuff.parse("<MyStuff />").items,{})

        MyStuff.items.maxlength = 1
        self.assertEquals(len(MyStuff.parse("<MyStuff><item name='hi' value='world' /></MyStuff>").items),1)
        self.assertRaises(dexml.ParseError,MyStuff.parse,"<MyStuff><item name='hi' value='world' /><item name='hello' value='earth' /></MyStuff>")
        s = MyStuff()
        s.items = [item(name="yo",value="dawg"),item(name="wazzup",value="yo")]
        self.assertRaises(dexml.RenderError,s.render)

        MyStuff.items.maxlength = None
        MyStuff.items.minlength = 2
        MyStuff.items.required = True
        self.assertEquals(len(MyStuff.parse("<MyStuff><item name='hi' value='world' /><item name='hello' value='earth' /></MyStuff>").items),2)
        self.assertRaises(dexml.ParseError,MyStuff.parse,"<MyStuff><item name='hi' value='world' /></MyStuff>")

        s = MyStuff()
        s.items = [item(name="yo",value="dawg")]
        self.assertRaises(dexml.RenderError,s.render)


    def test_choice_field(self):
        """Test operation of fields.Choice"""
        class breakfast(dexml.Model):
            meal = fields.Choice("bacon","cereal")
        class bacon(dexml.Model):
            num_rashers = fields.Integer()
        class cereal(dexml.Model):
            with_milk = fields.Boolean()

        b = breakfast.parse("<breakfast><bacon num_rashers='4' /></breakfast>")
        self.assertEquals(b.meal.num_rashers,4)

        b = breakfast.parse("<breakfast><cereal with_milk='true' /></breakfast>")
        self.assertTrue(b.meal.with_milk)

        self.assertRaises(dexml.ParseError,b.parse,"<breakfast><eggs num='2' /></breakfast>")
        self.assertRaises(dexml.ParseError,b.parse,"<breakfast />")

        b = breakfast()
        self.assertRaises(dexml.RenderError,b.render)
        b.meal = bacon(num_rashers=1)
        self.assertEquals(b.render(fragment=True),"<breakfast><bacon num_rashers=\"1\" /></breakfast>")


    def test_choice_field_sanity_checks(self):
        try:
            class SaneChoice(dexml.Model):
                item = fields.Choice(fields.String(),fields.Integer())
            assert False, "Choice field failed its sanity checks"
        except ValueError:
            pass
        class GreedyModel(fields.Model):
            def parse_child_node(self,obj,node):
                return dexml.PARSE_MORE
        class SaneChoice(dexml.Model):
            item = fields.Choice(GreedyModel("SaneChoice"))
            
        self.assertRaises(ValueError,SaneChoice.parse,"<SaneChoice><SaneChoice /></SaneChoice>")


    def test_list_of_choice(self):
        """Test operation of fields.Choice inside fields.List"""
        class breakfast(dexml.Model):
            meals = fields.List(fields.Choice("bacon","cereal"))
        class bacon(dexml.Model):
            num_rashers = fields.Integer()
        class cereal(dexml.Model):
            with_milk = fields.Boolean()

        b = breakfast.parse("<breakfast><bacon num_rashers='4' /></breakfast>")
        self.assertEquals(len(b.meals),1)
        self.assertEquals(b.meals[0].num_rashers,4)

        b = breakfast.parse("<breakfast><bacon num_rashers='2' /><cereal with_milk='true' /></breakfast>")
        self.assertEquals(len(b.meals),2)
        self.assertEquals(b.meals[0].num_rashers,2)
        self.assertTrue(b.meals[1].with_milk)


    def test_empty_only_boolean(self):
        """Test operation of fields.Boolean with empty_only=True"""
        class toggles(dexml.Model):
            toggle_str = fields.Boolean(required=False)
            toggle_empty = fields.Boolean(tagname=True,empty_only=True)

        t = toggles.parse("<toggles />")
        self.assertFalse(t.toggle_str)
        self.assertFalse(t.toggle_empty)

        t = toggles.parse("<toggles toggle_str=''><toggle_empty /></toggles>")
        self.assertTrue(t.toggle_str)
        self.assertTrue(t.toggle_empty)

        t = toggles.parse("<toggles toggle_str='no'><toggle_empty /></toggles>")
        self.assertFalse(t.toggle_str)
        self.assertTrue(t.toggle_empty)

        self.assertRaises(ValueError,toggles.parse,"<toggles><toggle_empty>no</toggle_empty></toggles>")
        self.assertFalse("toggle_empty" in toggles(toggle_empty=False).render())
        self.assertTrue("<toggle_empty />" in toggles(toggle_empty=True).render())

    def test_XmlNode(self):
        """Test correct operation of fields.XmlNode."""
        class bucket(dexml.Model):
            class meta:
                namespace = "bucket-uri"
            contents = fields.XmlNode(encoding="utf8")
        b = bucket.parse("<B:bucket xmlns:B='bucket-uri'><B:contents><hello><B:world /></hello></B:contents></B:bucket>")
        self.assertEquals(b.contents.childNodes[0].tagName,"hello")
        self.assertEquals(b.contents.childNodes[0].namespaceURI,None)
        self.assertEquals(b.contents.childNodes[0].childNodes[0].localName,"world")
        self.assertEquals(b.contents.childNodes[0].childNodes[0].namespaceURI,"bucket-uri")

        b = bucket()
        b.contents = "<hello>world</hello>"
        b = bucket.parse(b.render())
        self.assertEquals(b.contents.tagName,"hello")
        b.contents = u"<hello>world</hello>"
        b = bucket.parse(b.render())
        self.assertEquals(b.contents.tagName,"hello")

        b = bucket.parse("<bucket xmlns='bucket-uri'><bucket><hello /></bucket></bucket>")
        b2 = bucket.parse("".join(fields.XmlNode.render_children(b,b.contents,{})))
        self.assertEquals(b2.contents.tagName,"hello")

        class bucket(dexml.Model):
            class meta:
                namespace = "bucket-uri"
            contents = fields.XmlNode(tagname="contents")
        b = bucket.parse("<B:bucket xmlns:B='bucket-uri'><ignoreme /><B:contents><hello><B:world /></hello></B:contents></B:bucket>")
        self.assertEquals(b.contents.childNodes[0].tagName,"hello")


    def test_namespaced_attrs(self):
        class nsa(dexml.Model):
            f1 = fields.Integer(attrname=("test:","f1"))
        n = nsa.parse("<nsa t:f1='7' xmlns:t='test:' />")
        self.assertEquals(n.f1,7)
        n2 = nsa.parse(n.render())
        self.assertEquals(n2.f1,7)

        class nsa_decl(dexml.Model):
            class meta:
                tagname = "nsa"
                namespace = "test:"
                namespace_prefix = "t"
            f1 = fields.Integer(attrname=("test:","f1"))
        n = nsa_decl.parse("<t:nsa t:f1='7' xmlns:t='test:' />")
        self.assertEquals(n.f1,7)
        self.assertEquals(n.render(fragment=True),'<t:nsa xmlns:t="test:" t:f1="7" />')


    def test_namespaced_children(self):
        class nsc(dexml.Model):
            f1 = fields.Integer(tagname=("test:","f1"))
        n = nsc.parse("<nsc xmlns:t='test:'><t:f1>7</t:f1></nsc>")
        self.assertEquals(n.f1,7)
        n2 = nsc.parse(n.render())
        self.assertEquals(n2.f1,7)

        n = nsc.parse("<nsc><f1 xmlns='test:'>7</f1></nsc>")
        self.assertEquals(n.f1,7)
        n2 = nsc.parse(n.render())
        self.assertEquals(n2.f1,7)

        class nsc_decl(dexml.Model):
            class meta:
                tagname = "nsc"
                namespace = "test:"
                namespace_prefix = "t"
            f1 = fields.Integer(tagname=("test:","f1"))
        n = nsc_decl.parse("<t:nsc xmlns:t='test:'><t:f1>7</t:f1></t:nsc>")
        self.assertEquals(n.f1,7)
        n2 = nsc_decl.parse(n.render())
        self.assertEquals(n2.f1,7)

        n = nsc_decl.parse("<nsc xmlns='test:'><f1>7</f1></nsc>")
        self.assertEquals(n.f1,7)
        n2 = nsc_decl.parse(n.render())
        self.assertEquals(n2.f1,7)

        self.assertEquals(n2.render(fragment=True),'<t:nsc xmlns:t="test:"><t:f1>7</t:f1></t:nsc>')


    def test_order_sensitive(self):
        """Test operation of order-sensitive and order-insensitive parsing"""
        class junk(dexml.Model):
            class meta:
                order_sensitive = True
            name = fields.String(tagname=True)
            notes = fields.List(fields.String(tagname="note"))
            amount = fields.Integer(tagname=True)
        class junk_unordered(junk):
            class meta:
                tagname = "junk"
                order_sensitive = False

        j = junk.parse("<junk><name>test1</name><note>note1</note><note>note2</note><amount>7</amount></junk>")
        self.assertEquals(j.name,"test1")
        self.assertEquals(j.notes,["note1","note2"])
        self.assertEquals(j.amount,7)

        j = junk_unordered.parse("<junk><name>test1</name><note>note1</note><note>note2</note><amount>7</amount></junk>")
        self.assertEquals(j.name,"test1")
        self.assertEquals(j.notes,["note1","note2"])
        self.assertEquals(j.amount,7)

        self.assertRaises(dexml.ParseError,junk.parse,"<junk><note>note1</note><amount>7</amount><note>note2</note><name>test1</name></junk>")

        j = junk_unordered.parse("<junk><note>note1</note><amount>7</amount><note>note2</note><name>test1</name></junk>")
        self.assertEquals(j.name,"test1")
        self.assertEquals(j.notes,["note1","note2"])
        self.assertEquals(j.amount,7)


    def test_namespace_prefix_generation(self):
        class A(dexml.Model):
            class meta:
                namespace='http://xxx'
            a = fields.String(tagname=('http://yyy','a'))
        class B(dexml.Model):
            class meta:
                namespace='http://yyy'
            b = fields.Model(A)

        b1 = B(b=A(a='value'))

        #  With no specific prefixes set we can't predict the output,
        #  but it should round-trip OK.
        assert model_fields_equal(B.parse(b1.render()),b1)

        #  With specific prefixes set, output is predictable.
        A.meta.namespace_prefix = "x"
        B.meta.namespace_prefix = "y"
        self.assertEquals(b1.render(),'<?xml version="1.0" ?><y:B xmlns:y="http://yyy"><x:A xmlns:x="http://xxx"><y:a>value</y:a></x:A></y:B>')
        A.meta.namespace_prefix = None
        B.meta.namespace_prefix = None

        #  This is a little hackery to trick the random-prefix generator
        #  into looping a few times before picking one.  We can't predict
        #  the output but it'll exercise the code.
        class pickydict(dict):
            def __init__(self,*args,**kwds):
                self.__counter = 0
                super(pickydict,self).__init__(*args,**kwds)
            def __contains__(self,key):
                if self.__counter > 5:
                    return super(pickydict,self).__contains__(key)
                self.__counter += 1
                return True
        assert model_fields_equal(B.parse(b1.render(nsmap=pickydict())),b1)

        class A(dexml.Model):
            class meta:
                namespace='T:'
            a = fields.String(attrname=('A:','a'))
            b = fields.String(attrname=(None,'b'))
            c = fields.String(tagname=(None,'c'))

        a1 = A(a="hello",b="world",c="owyagarn")

        #  With no specific prefixes set we can't predict the output,
        #  but it should round-trip OK.
        assert model_fields_equal(A.parse(a1.render()),a1)

        #  With specific prefixes set, output is predictable.
        #  Note that this suppresses generation of the xmlns declarations,
        #  so the output is actually broken here.  Broken, but predictable.
        nsmap = {}
        nsmap["T"] = ["T:"]
        nsmap["A"] = ["A:"]
        self.assertEquals(a1.render(fragment=True,nsmap=nsmap),'<A xmlns="T:" A:a="hello" b="world"><c xmlns="">owyagarn</c></A>')

        #  This is a little hackery to trick the random-prefix generator
        #  into looping a few times before picking one.  We can't predict
        #  the output but it'll exercise the code.
        class pickydict(dict):
            def __init__(self,*args,**kwds):
                self.__counter = 0
                super(pickydict,self).__init__(*args,**kwds)
            def __contains__(self,key):
                if self.__counter > 5:
                    return super(pickydict,self).__contains__(key)
                self.__counter += 1
                return True
        assert model_fields_equal(A.parse(a1.render(nsmap=pickydict())),a1)

        A.c.tagname = ("C:","c")
        assert model_fields_equal(A.parse(a1.render(nsmap=pickydict())),a1)
        a1 = A(a="hello",b="world",c="")
        assert model_fields_equal(A.parse(a1.render(nsmap=pickydict())),a1)


    def test_parsing_value_from_tag_contents(self):
        class attr(dexml.Model):
            name = fields.String()
            value = fields.String(tagname=".")
        class obj(dexml.Model):
            id = fields.String()
            attrs = fields.List(attr)
        o = obj.parse('<obj id="z108"><attr name="level">6</attr><attr name="descr">description</attr></obj>')
        self.assertEquals(o.id,"z108")
        self.assertEquals(len(o.attrs),2)
        self.assertEquals(o.attrs[0].name,"level")
        self.assertEquals(o.attrs[0].value,"6")
        self.assertEquals(o.attrs[1].name,"descr")
        self.assertEquals(o.attrs[1].value,"description")

        o = obj(id="test")
        o.attrs.append(attr(name="hello",value="world"))
        o.attrs.append(attr(name="wherethe",value="bloodyhellareya"))
        self.assertEquals(o.render(fragment=True),'<obj id="test"><attr name="hello">world</attr><attr name="wherethe">bloodyhellareya</attr></obj>')


    def test_inheritance_of_meta_attributes(self):
        class Base1(dexml.Model):
            class meta:
                tagname = "base1"
                order_sensitive = True
        class Base2(dexml.Model):
            class meta:
                tagname = "base2"
                order_sensitive = False

        class Sub(Base1):
            pass
        self.assertEquals(Sub.meta.order_sensitive,True)

        class Sub(Base2):
            pass
        self.assertEquals(Sub.meta.order_sensitive,False)

        class Sub(Base2):
            class meta:
                order_sensitive = True
        self.assertEquals(Sub.meta.order_sensitive,True)

        class Sub(Base1,Base2):
            pass
        self.assertEquals(Sub.meta.order_sensitive,True)

        class Sub(Base2,Base1):
            pass
        self.assertEquals(Sub.meta.order_sensitive,False)


    def test_mixing_in_other_base_classes(self):
        class Thing(dexml.Model):
            testit = fields.String()
        class Mixin(object):
            def _get_testit(self):
                return 42
            def _set_testit(self,value):
                pass
            testit = property(_get_testit,_set_testit)

        class Sub(Thing,Mixin):
            pass
        assert issubclass(Sub,Thing)
        assert issubclass(Sub,Mixin)
        s = Sub.parse('<Sub testit="hello" />')
        self.assertEquals(s.testit,"hello")

        class Sub(Mixin,Thing):
            pass
        assert issubclass(Sub,Thing)
        assert issubclass(Sub,Mixin)
        s = Sub.parse('<Sub testit="hello" />')
        self.assertEquals(s.testit,42)


    def test_error_using_undefined_model_class(self):
        class Whoopsie(dexml.Model):
            value = fields.Model("UndefinedModel")
        self.assertRaises(ValueError,Whoopsie.parse,"<Whoopsie><UndefinedModel /></Whoopsie>")
        self.assertRaises(ValueError,Whoopsie,value=None)

        class Whoopsie(dexml.Model):
            value = fields.Model((None,"UndefinedModel"))
        self.assertRaises(ValueError,Whoopsie.parse,"<Whoopsie><UndefinedModel /></Whoopsie>")
        self.assertRaises(ValueError,Whoopsie,value=None)

        class Whoopsie(dexml.Model):
            value = fields.Model(("W:","UndefinedModel"))
        self.assertRaises(ValueError,Whoopsie.parse,"<Whoopsie><UndefinedModel /></Whoopsie>")
        self.assertRaises(ValueError,Whoopsie,value=None)


    def test_unordered_parse_of_list_field(self):
        class Notebook(dexml.Model):
            class meta:
                order_sensitive = False
            notes = fields.List(fields.String(tagname="note"),tagname="notes")

        n = Notebook.parse("<Notebook><notes><note>one</note><note>two</note></notes></Notebook>")
        self.assertEquals(n.notes,["one","two"])

        Notebook.parse("<Notebook><wtf /><notes><note>one</note><note>two</note><wtf /></notes></Notebook>")

        Notebook.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError,Notebook.parse,"<Notebook><wtf /><notes><note>one</note><note>two</note><wtf /></notes></Notebook>")
        self.assertRaises(dexml.ParseError,Notebook.parse,"<Notebook tag='home'><notes><note>one</note><note>two</note></notes></Notebook>")

