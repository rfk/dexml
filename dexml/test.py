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
        doctest.testmod(dexml)

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
        class pets(dexml.Model):
            person = fields.Model()
            pets = fields.List("pet",minlength=1)
            notes = fields.List(fields.String(tagname="note"),maxlength=2)

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

