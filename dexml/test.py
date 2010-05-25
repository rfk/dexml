"""

  dexml.test:  testcases for dexml module.

"""

import os
import os.path
import difflib
import unittest
import doctest

import dexml
from dexml import fields


class TestDexmlDocstring(unittest.TestCase):

    def test_docstring(self):
        """Test dexml docstrings"""
        assert doctest.testmod(dexml)[0] == 0

    def test_readme_matches_docstring(self):
        """Test that the README matches the main docstring."""
        readme = os.path.join(os.path.dirname(__file__),"../README.txt")
        if os.path.exists(readme):
            diff = difflib.unified_diff(open(readme).readlines(),dexml.__doc__.splitlines(True))
            diff = "".join(diff)
            if diff:
                print diff
                raise AssertionError, "README doesn't match docstring"


class TestDexml(unittest.TestCase):

    def test_base(self):
        """Test operation of a dexml.Model class with no fields."""
        class hello(dexml.Model):
            pass

        h = hello.parse("<hello />")
        self.assertTrue(h)

        h = hello.parse("<hello></hello>")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.parse,"<Hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<hllo />")

        h = hello.parse("<hello>world</hello>")
        self.assertTrue(h)

        hello.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError,hello.parse,"<hello>world</hello>")
        hello.meta.ignore_unknown_elements = True

        h = hello()
        self.assertEquals(h.render(),'<?xml version="1.0" ?><hello />')

        h = hello()
        self.assertEquals(h.render(fragment=True),"<hello />")


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

        h = hello()
        self.assertEquals(h.render(fragment=True),'<hello xmlns="http://hello.com/" />')

        hello.meta.namespace_prefix = "H"
        self.assertEquals(h.render(fragment=True),'<H:hello xmlns:H="http://hello.com/" />')


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


    def test_model_field(self):
        """Test operation of fields.Model."""
        class person(dexml.Model):
            name = fields.String()
            age = fields.Integer()
        class pet(dexml.Model):
            name = fields.String()
            species = fields.String(required=False)
        class pets(dexml.Model):
            person = fields.Model()
            pet1 = fields.Model("pet")
            pet2 = fields.Model(pet,required=False)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.species,"dog")
        self.assertEquals(p.pet2,None)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><pet name='fishy' species='fish' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pet1.name,"riley")
        self.assertEquals(p.pet2.species,"fish")

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
        p.pet2 = pet(name="guppy",species="fish")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /></pets>')


    def test_model_field_namespace(self):
        """Test operation of fields.Model with namespaces"""
        class petbase(dexml.Model):
            class meta:
                namespace = "http://www.pets.com/PetML"
                namespace_prefix = "P"
        class person(petbase):
            name = fields.String()
            age = fields.Integer()
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
            rewards = fields.List("reward", tagname = "rewards")

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /></pets>")
        self.assertEquals(p.person.name,"ryan")
        self.assertEquals(p.pets[0].species,"dog")
        self.assertEquals(len(p.pets),1)
        self.assertEquals(len(p.notes),0)

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><pet name='fishy' species='fish' /><note>noted</note></pets>")
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

        p = pets.parse("<pets><person name='ryan' age='26'/><pet name='riley' species='dog' /><rewards><reward date='February 23, 2010'/><reward date='November 10, 2009'/></rewards></pets>")
        self.assertEquals(len(p.rewards), 2)
        self.assertEquals(p.rewards[1].date, 'November 10, 2009')
        self.assertEquals(p.render(fragment = True), '<pets><person name="ryan" age="26" /><pet name="riley" species="dog" /><rewards><reward date="February 23, 2010" /><reward date="November 10, 2009" /></rewards></pets>')

        pets.meta.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError, pets.parse, "<pets><person name='ryan' age='26' /><pet name='riley' species='dog' /><reward date='February 23, 2010'/><reward date='November 10, 2009' /></pets>")

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
            items = fields.Dict('item', key = 'name', unique = True)
        xml = '<obj><item name="item1"><attr>val1</attr></item><item name="item1"><attr>val2</attr></item></obj>'
        self.assertRaises(dexml.ParseError, obj.parse, xml)

        class obj(dexml.Model):
            items = fields.Dict('item', key = 'name', tagname = 'items')
        xml = '<obj><items><item name="item1"><attr>val1</attr></item><item name="item2"><attr>val2</attr></item></items></obj>'

        o = obj.parse(xml)
        self.assertEquals(len(o.items), 2)
        self.assertEquals(o.items['item1'].name, 'item1')
        self.assertEquals(o.items['item2'].attr, 'val2')
        del o.items['item2']
        self.assertEquals(o.render(fragment = True), '<obj><items><item name="item1"><attr>val1</attr></item></items></obj>')

        from collections import defaultdict
        class _dict(defaultdict):
            def __init__(self):
                super(_dict, self).__init__(item)

        class obj(dexml.Model):
            items = fields.Dict('item', key = 'name', dictclass = _dict)
        o = obj()
        self.assertEquals(o.items['item1'].name, 'item1')

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
        b.meal = bacon(num_rashers=1)
        self.assertEquals(b.render(fragment=True),"<breakfast><bacon num_rashers=\"1\" /></breakfast>")


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
            contents = fields.XmlNode()
        b = bucket.parse("<B:bucket xmlns:B='bucket-uri'><B:contents><hello><B:world /></hello></B:contents></B:bucket>")
        self.assertEquals(b.contents.childNodes[0].tagName,"hello")
        self.assertEquals(b.contents.childNodes[0].namespaceURI,None)
        self.assertEquals(b.contents.childNodes[0].childNodes[0].localName,"world")
        self.assertEquals(b.contents.childNodes[0].childNodes[0].namespaceURI,"bucket-uri")

        b = bucket()
        b = bucket.parse("<bucket xmlns='bucket-uri'><bucket><hello /></bucket></bucket>")
        b2 = bucket.parse("".join(fields.XmlNode.render_children(b,b.contents,{})))
        self.assertEquals(b2.contents.tagName,"hello")

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
                namespace_prefix='x'
            a = fields.String(tagname=('http://yyy','a'))
        class B(dexml.Model):
            class meta:
                namespace='http://yyy'
                namespace_prefix='y'
            b = fields.Model(A)
        b1 = B(b=A(a='value'))
        self.assertEquals(b1.render(),'<?xml version="1.0" ?><y:B xmlns:y="http://yyy"><x:A xmlns:x="http://xxx"><y:a>value</y:a></x:A></y:B>')

