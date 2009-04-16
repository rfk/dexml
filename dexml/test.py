
import unittest
import dexml
from dexml import fields


class TestDexml(unittest.TestCase):

    def test_base(self):
        """Test operation of a dexml.Base class with no fields."""
        class hello(dexml.Base):
            pass
        h = hello.dexml("<hello />")
        self.assertTrue(h)
        h = hello.dexml("<hello></hello>")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.dexml,"<Hello />")
        self.assertRaises(dexml.ParseError,hello.dexml,"<hllo />")
        self.assertRaises(dexml.ParseError,hello.dexml,"<hello>world</hello>")
        h = hello()
        self.assertEquals(h.rexml(),'<?xml version="1.0" ?><hello />')
        h = hello()
        self.assertEquals(h.rexml(fragment=True),"<hello />")

    def test_namespace(self):
        """Test handling of namespaces."""
        class hello(dexml.Base):
            class meta:
                namespace = "http://hello.com/"
        # Test parsing
        h = hello.dexml("<hello xmlns='http://hello.com/' />")
        self.assertTrue(h)
        h = hello.dexml("<H:hello xmlns:H='http://hello.com/' />")
        self.assertTrue(h)
        self.assertRaises(dexml.ParseError,hello.dexml,"<hello />")
        self.assertRaises(dexml.ParseError,hello.dexml,"<H:hllo xmlns:H='http://hello.com/' />")
        self.assertRaises(dexml.ParseError,hello.dexml,"<H:hello xmlns:H='http://hello.com/'>world</H:hello>")
        # Test rendering
        h = hello()
        self.assertEquals(h.rexml(fragment=True),'<hello xmlns="http://hello.com/" />')
        hello._meta.namespace_prefix = "H"
        self.assertEquals(h.rexml(fragment=True),'<H:hello xmlns:H="http://hello.com/" />')

    def test_value_fields(self):
        """Test operation of basic value fields."""
        class hello(dexml.Base):
            recipient = fields.String()
            sentby = fields.String(attrname="sender")
            strength = fields.Integer(default=1)
            message = fields.String(tagname="message")
        #  Test parsing
        h = hello.dexml("<hello recipient='ryan' sender='lozz' strength='7'><message>hi there</message></hello>")
        self.assertEquals(h.recipient,"ryan")
        self.assertEquals(h.sentby,"lozz")
        self.assertEquals(h.message,"hi there")
        self.assertEquals(h.strength,7)
        h = hello.dexml("<hello recipient='ryan' sender='lozz'><message>hi there</message></hello>")
        self.assertEquals(h.recipient,"ryan")
        self.assertEquals(h.sentby,"lozz")
        self.assertEquals(h.message,"hi there")
        self.assertEquals(h.strength,1)
        self.assertRaises(dexml.ParseError,hello.dexml,"<hello recipient='ryan'><message>hi there</message></hello>")
        self.assertRaises(dexml.ParseError,hello.dexml,"<hello recipient='ryan' sender='lozz'><message>hi there</message><extra>how are you</extra></hello>")
        self.assertRaises(dexml.ParseError,hello.dexml,"<hello recipient='ryan' sender='lozz'><extra>how are you</extra></hello>")
        # Test rendering
        h = hello()
        self.assertRaises(dexml.RenderError,h.rexml)
        h.recipient = "lozz"
        h.sentby = "ryan"
        h.message = "hello yourself"
        self.assertEquals(h.rexml(fragment=True),'<hello recipient="lozz" sender="ryan"><message>hello yourself</message></hello>')
        h.strength = 5
        self.assertEquals(h.rexml(fragment=True),'<hello recipient="lozz" sender="ryan" strength="5"><message>hello yourself</message></hello>')
        h.strength = 1
        self.assertEquals(h.rexml(fragment=True),'<hello recipient="lozz" sender="ryan"><message>hello yourself</message></hello>')
        h.strength = None
        self.assertEquals(h.rexml(fragment=True),'<hello recipient="lozz" sender="ryan"><message>hello yourself</message></hello>')


