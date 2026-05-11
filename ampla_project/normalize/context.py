from __future__ import annotations

from dataclasses import dataclass, field

from lxml.etree import Element


@dataclass
class NormalizationContext:
    """
    Central context object used during normalization.
    Replaces all XSLT global variables, keys, and computed values.
    """

    root: Element
    language_doc: Element | None

    # Computed values
    default_display_order: int = 0
    translations: dict[str, str] = field(default_factory=dict)

    # Indexes (equivalent to xsl:key)
    items_by_id: dict[str, Element] = field(default_factory=dict)
    items_by_type: dict[str, list[Element]] = field(default_factory=dict)
    items_by_reference: dict[str, list[Element]] = field(default_factory=dict)
    classes_by_id: dict[str, Element] = field(default_factory=dict)

    def __post_init__(self):
        self._compute_default_display_order()
        self._load_translations()
        self._index_items()
        self._index_classes()

    def _compute_default_display_order(self):
        """
        Equivalent to XSLT:
            <xsl:variable name="platformVersion" ...>
            <xsl:variable name="majorVersion" ...>
            <xsl:variable name="minorVersion" ...>
            if major > 4 or (major == 4 and minor >= 2) → 50000 else 0
        """
        ref = self.root.find("Reference[@name='Citect.Ampla.StandardItems']")
        if ref is None:
            self.default_display_order = 0
            return

        version = ref.get("version", "0.0")
        parts = version.split(".")
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0

        if major > 4 or (major == 4 and minor >= 2):
            self.default_display_order = 50000
        else:
            self.default_display_order = 0

    def _load_translations(self):
        """
        Loads translation entries from the language document.
        XSLT uses: document($language)/html/body/div[@id]
        """
        if self.language_doc is None:
            return

        for div in self.language_doc.findall(".//div[@id]"):
            key = div.get("id")
            value = (div.text or "").strip()
            if key and value:
                self.translations[key] = value

    def get_translation(self, name: str | None) -> str | None:
        if not name:
            return None
        translated = self.translations.get(name)
        if translated == name:
            return None
        return translated

    def _index_items(self):
        """
        Build indexes equivalent to:
            key('items-by-id')
            key('items-by-type')
            key('items-by-reference')
        """
        for elem in self.root.findall(".//Item[@id]"):
            item_id = elem.get("id")
            item_type = elem.get("type")
            reference = elem.get("reference")

            if item_id:
                self.items_by_id[item_id] = elem

            if item_type:
                self.items_by_type.setdefault(item_type, []).append(elem)

            if reference:
                self.items_by_reference.setdefault(reference, []).append(elem)

    def _index_classes(self):
        """
        Equivalent to key('class-by-id')
        """
        for elem in self.root.findall(".//ClassDefinition[@id]"):
            class_id = elem.get("id")
            if class_id:
                self.classes_by_id[class_id] = elem

    def generate_hash(self, full_name: str) -> str:
        """
        XSLT uses generate-id(), which is unstable.
        We replace it with a stable hash of the fullName.
        """
        import hashlib

        return hashlib.md5(full_name.encode("utf-8")).hexdigest()[:8]
