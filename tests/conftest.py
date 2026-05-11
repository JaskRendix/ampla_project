import pytest
from lxml.etree import fromstring, parse

from ampla_project.model.item import Item, ItemLink, Property
from ampla_project.normalize import normalize
from ampla_project.normalize.context import NormalizationContext
from tests.utils.fakes import FakeItem, FakeItemLink, FakeProperty


@pytest.fixture
def xml_from_string():
    """Return a function that parses XML text into an lxml Element."""
    return fromstring


@pytest.fixture
def xml_from_file():
    """Return a function that parses an XML file path into an lxml Element."""

    def loader(path):
        return parse(path).getroot()

    return loader


@pytest.fixture
def normalizer():
    """Return the top-level normalize function."""
    return normalize


@pytest.fixture
def normalize_xml(normalizer):
    """Return a helper that normalizes XML text directly."""

    def factory(xml_text, language_text=None):
        root = fromstring(xml_text)
        language_doc = fromstring(language_text) if language_text else None
        return normalizer(root, language_doc)

    return factory


@pytest.fixture
def context_factory():
    """Return a factory for NormalizationContext instances."""

    def factory(root, language_doc=None):
        return NormalizationContext(root=root, language_doc=language_doc)

    return factory


@pytest.fixture
def item_factory():
    """Return a helper for building normalized Item objects."""

    def factory(
        item_id,
        name=None,
        type_="Test",
        full_name=None,
        hash=None,
        definition=None,
        translation=None,
        properties=None,
    ):
        name = name or item_id
        full_name = full_name or name
        hash = hash or f"hash:{full_name}"
        return Item(
            id=item_id,
            name=name,
            type=type_,
            full_name=full_name,
            hash=hash,
            definition=definition,
            translation=translation,
            properties=properties or {},
        )

    return factory


@pytest.fixture
def itemlink_factory():
    """Return a helper for building ItemLink objects."""

    def factory(
        target_id=None,
        absolute_path=None,
        property_name=None,
        relative_path=None,
        broken_target=False,
        broken_absolute=False,
        broken_relative=False,
        event=None,
        handler=None,
        expression_match=None,
    ):
        link = ItemLink(
            target_id=target_id,
            absolute_path=absolute_path,
            property_name=property_name,
            broken_target=broken_target,
            broken_absolute=broken_absolute,
            broken_relative=broken_relative,
            relative_path=relative_path,
        )
        link.event = event
        link.handler = handler
        link.expression_match = expression_match
        return link

    return factory


@pytest.fixture
def property_factory():
    """Return a helper for building Property objects."""

    def factory(name, value=None, attributes=None, item_links=None):
        return Property(
            name=name,
            value=value,
            attributes=attributes or {},
            item_links=item_links or [],
        )

    return factory


@pytest.fixture
def fake_item():
    return FakeItem


@pytest.fixture
def fake_item_link():
    return FakeItemLink


@pytest.fixture
def fake_property():
    return FakeProperty
