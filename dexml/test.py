
import unittest
import dexml
from dexml import fields


class TestDexml(unittest.TestCase):

    def test_base(self):
        """Test operation of a dexml.Base class with no fields."""
        class hello(dexml.Base):
            pass
        h = hello.parse("<hello />")
        self.assertTrue(h)
        h = hello.parse("<hello></hello>")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.parse,"<Hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<hllo />")
        h = hello.parse("<hello>world</hello>")
        self.assertTrue(h)
        hello.ignore_unknown_elements = False
        self.assertRaises(dexml.ParseError,hello.parse,"<hello>world</hello>")
        hello.ignore_unknown_elements = True
        h = hello()
        self.assertEquals(h.render(),'<?xml version="1.0" ?><hello />')
        h = hello()
        self.assertEquals(h.render(fragment=True),"<hello />")

    def test_namespace(self):
        """Test handling of namespaces."""
        class hello(dexml.Base):
            ignore_unknown_elements = False
            class meta:
                namespace = "http://hello.com/"
        # Test parsing
        h = hello.parse("<hello xmlns='http://hello.com/' />")
        self.assertTrue(h)
        h = hello.parse("<H:hello xmlns:H='http://hello.com/' />")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.parse,"<hello />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hllo xmlns:H='http://hello.com/' />")
        self.assertRaises(dexml.ParseError,hello.parse,"<H:hello xmlns:H='http://hello.com/'>world</H:hello>")
        # Test rendering
        h = hello()
        self.assertEquals(h.render(fragment=True),'<hello xmlns="http://hello.com/" />')
        hello._meta.namespace_prefix = "H"
        self.assertEquals(h.render(fragment=True),'<H:hello xmlns:H="http://hello.com/" />')


    def test_value_fields(self):
        """Test operation of basic value fields."""
        class hello(dexml.Base):
            recipient = fields.String()
            sentby = fields.String(attrname="sender")
            strength = fields.Integer(default=1)
            message = fields.String(tagname="message")
        #  Test parsing
        h = hello.parse("<hello recipient='ryan' sender='lozz' strength='7'><message>hi there</message></hello>")
        self.assertEquals(h.recipient,"ryan")
        self.assertEquals(h.sentby,"lozz")
        self.assertEquals(h.message,"hi there")
        self.assertEquals(h.strength,7)


    def test_item_field(self):
        """Test operation of fields.Item."""
        class person(dexml.Base):
            name = fields.String()
            age = fields.Integer()
        class pet(dexml.Base):
            name = fields.String()
            species = fields.String(required=False)
        class pets(dexml.Base):
            person = fields.Item()
            pet1 = fields.Item("pet")
            pet2 = fields.Item(pet,required=False)
        # Test parsing
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
        # Test rendering
        p = pets()
        self.assertRaises(dexml.RenderError,p.render)
        p.person = person(name="lozz",age="25")
        p.pet1 = pet(name="riley")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /></pets>')
        p.pet2 = pet(name="guppy",species="fish")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /></pets>')


    def test_item_field_namespace(self):
        """Test operation of fields.Item with namespaces"""
        class petbase(dexml.Base):
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
            person = fields.Item()
            pet1 = fields.Item("pet")
            pet2 = fields.Item(pet,required=False)
        # Test parsing
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
        # Test rendering
        p = pets()
        self.assertRaises(dexml.RenderError,p.render)
        p.person = person(name="lozz",age="25")
        p.pet1 = pet(name="riley")
        self.assertEquals(p.render(fragment=True),'<P:pets xmlns:P="http://www.pets.com/PetML"><P:person name="lozz" age="25" /><P:pet name="riley" /></P:pets>')
        p.pet2 = pet(name="guppy",species="fish")
        self.assertEquals(p.render(fragment=True),'<P:pets xmlns:P="http://www.pets.com/PetML"><P:person name="lozz" age="25" /><P:pet name="riley" /><P:pet name="guppy" species="fish" /></P:pets>')

    def test_list_field(self):
        """Test operation of fields.List"""
        class person(dexml.Base):
            name = fields.String()
            age = fields.Integer()
        class pet(dexml.Base):
            name = fields.String()
            species = fields.String(required=False)
        class pets(dexml.Base):
            person = fields.Item()
            pets = fields.List("pet",minlength=1)
            notes = fields.List(fields.String(tagname="note"),maxlength=2)
        # Test parsing
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
        # Test rendering
        p = pets()
        p.person = person(name="lozz",age="25")
        self.assertRaises(dexml.RenderError,p.render)
        p.pets.append(pet(name="riley"))
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /></pets>')
        p.pets.append(pet(name="guppy",species="fish"))
        p.notes.append("noted")
        self.assertEquals(p.render(fragment=True),'<pets><person name="lozz" age="25" /><pet name="riley" /><pet name="guppy" species="fish" /><note>noted</note></pets>')


