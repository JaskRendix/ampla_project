from lxml.etree import fromstring

from ampla_project.normalize.context import NormalizationContext
from ampla_project.normalize.properties import normalize_property


def test_csv_property_to_itemlinks():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="EquipmentTypes">A,B,C</Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop_elem = root.find("Property")
    prop = normalize_property(ctx, root, prop_elem)

    assert len(prop.item_links) == 3
    assert prop.item_links[0].absolute_path == "A"
    assert prop.item_links[1].absolute_path == "B"
    assert prop.item_links[2].absolute_path == "C"


def test_csv_property_skips_empty_segments():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="EquipmentTypes">A,, C ,</Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert [link.absolute_path for link in prop.item_links] == ["A", "C"]


def test_soap_property_returns_placeholder_and_flag():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="Description" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Envelope><soap:Body><Value>hello</Value></soap:Body></soap:Envelope>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert prop.value == "{SOAP}"
    assert prop.attributes["isSoap"] == "true"
    assert prop.item_links == []


def test_subscription_property_parses_optional_fields():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="MySubscription">1|/Area/Path|OnChange|Handler|MatchExpr</Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))
    link = prop.item_links[0]

    assert link.absolute_path == "/Area/Path"
    assert link.event == "OnChange"
    assert link.handler == "Handler"
    assert link.expression_match == "MatchExpr"


def test_subscription_property_ignores_invalid_lines():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="MySubscription">invalid-line-without-delimiters</Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert prop.item_links == []


def test_home_property_counts_home_favourites():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="Home">
        <Descriptor type="Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common">
          <Property name="LocationType">Home</Property>
        </Descriptor>
        <Descriptor type="Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common">
          <Property name="LocationType">Home</Property>
        </Descriptor>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert prop.value == "{2 Favourite(s)}"
    assert prop.item_links == []


def test_favorites_property_marks_corrupt_entries():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="Favorites">
        <Descriptor type="Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common">
          <Property name="LocationType">Favorite</Property>
        </Descriptor>
        <Descriptor type="Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common">
          <Property name="LocationType">Home</Property>
        </Descriptor>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert prop.value == "{2 Favourite(s)}"
    assert prop.attributes["isCorrupt"] == "true"


def test_cycle_manager_property_builds_item_links():
    xml = """
    <Item id="1" name="Test" type="Citect.Ampla.General.Server.RecordStates.CycleManager">
      <Property name="Cycles">
        <Property>
          <Item>cycle1</Item>
        </Property>
        <Property>
          <Item>cycle2</Item>
        </Property>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(ctx, root, root.find("Property"))

    assert [link.absolute_path for link in prop.item_links] == ["cycle1", "cycle2"]


def test_historical_expression_warning_sets_message_when_manual_and_empty_format():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="CaptureValueForManualRecords">True</Property>
      <Property name="RefreshOnManualEntry">True</Property>
      <Property name="HistoricalFieldExpression">
        <HistoricalExpressionConfig>
          <ExpressionConfig />
        </HistoricalExpressionConfig>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    prop = normalize_property(
        ctx, root, root.find("Property[@name='HistoricalFieldExpression']")
    )

    assert prop.attributes["message"] == "No expression specified for Manual records."


def test_expression_config_property_applies_normalization():
    xml = """
    <Item id="1" name="Test" type="X">
      <Property name="Check">
        <HistoricalExpressionConfig>
          <ExpressionConfig format="sum(#ItemReference0#)">
            <ItemLinkCollection>
              <ItemLink targetID="Missing" format="val(#ItemReference0#)" />
            </ItemLinkCollection>
          </ExpressionConfig>
        </HistoricalExpressionConfig>
      </Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    normalize_property(ctx, root, root.find("Property"))
    expr = root.find(".//ExpressionConfig")

    assert expr.get("text") == "sum(Project.[Missing:Missing])"
    assert (
        expr.find(".//ItemLink").get("expressionFormat")
        == "val(Project.[Missing:Missing])"
    )
