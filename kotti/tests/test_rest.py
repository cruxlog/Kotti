from kotti.resources import TypeInfo, Content
from kotti.rest import schema_factory
from kotti.testing import DummyRequest
from sqlalchemy import Column, ForeignKey, Integer
import colander
import json


class Something(Content):
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    type_info = TypeInfo(name="Something")


@schema_factory(Something)
def sa(context, request):
    return 'a'


@schema_factory(Something, name='b')
def sb(context, request):
    return 'b'


class TestSerializer:

    def test_serializes_decorator(self, config):
        from kotti.rest import ISchemaFactory
        from zope.component import getUtility

        config.scan('kotti.tests.test_rest')
        obj, req = Something(), DummyRequest()

        assert getUtility(ISchemaFactory,
                          name='Something/default')(obj, req) == 'a'
        assert getUtility(ISchemaFactory,
                          name='Something/b')(obj, req) == 'b'


class TestSerializeDefaultContent:

    def make_one(self, config, klass=Content, **kw):
        from kotti.rest import serialize

        config.scan('kotti.rest')

        props = {
            'name': 'doc-a',
            'title': u'Doc A',
            'description': u'desc...'
        }
        props.update(**kw)
        obj = klass(**props)
        return serialize(obj, DummyRequest())

    def test_serialize_content(self, config):
        from kotti.resources import Content
        assert self.make_one(config, klass=Content) == {
            'id': u'doc-a',
            'title': u'Doc A',
            'tags': colander.null,
            'description': u'desc...',
        }

    def test_serialize_document(self, config):
        from kotti.resources import Document

        assert self.make_one(config, Document, body=u'Body text') == {
            'id': u'doc-a',
            'title': u'Doc A',
            'tags': colander.null,
            'description': u'desc...',
            'body': u'Body text',
        }

    def test_serialize_file(self, config, filedepot):
        from kotti.resources import File
        res = self.make_one(config, File, data='file content')
        assert res  # TODO: finish

    # TODO: serializing an image


class TestRestView:
    def get_view(self, context, request, name):
        from pyramid.compat import map_
        from pyramid.interfaces import IView
        from pyramid.interfaces import IViewClassifier
        from zope.interface import providedBy

        provides = [IViewClassifier] + map_(
            providedBy,
            (request, context)
        )

        return request.registry.adapters.lookup(provides, IView, name=name)

    def test_predicate_matching(self, config):
        from kotti.resources import Document
        from kotti.rest import ACCEPT
        from webob.acceptparse import MIMEAccept

        config.include('kotti.rest')

        req = DummyRequest(accept=MIMEAccept(ACCEPT))
        doc = Document()

        view = self.get_view(doc, req, name='json')
        resp = view(doc, req)
        assert resp.json

    def test_jsonp_as_renderer(self, config):
        from pyramid.renderers import render
        from kotti.resources import Document

        config.include('kotti.rest')

        doc = Document('1')
        req = DummyRequest()

        assert json.loads(render('kotti_jsonp', doc, request=req)) == {
            "body": "1",
            "tags": None,
            "id": None,
            "description": "",
            "title": ""
        }
