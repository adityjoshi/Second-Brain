import json
import re
from pathlib import Path

from config import constants

DOCUMENT_NAME_CANDIDATES = ("file_name", "filename", "file", "pdf_file", "pdf", "document",
                            "path")
SECTION_CANDIDATES = ("sections", "section_headings", "headings")
HEADING_LINE_PATTERN = re.compile(r"^[ \t]*([A-Z][A-Z0-9 &/,()'-]{3,})[ \t]*$", re.MULTILINE)


class UnreadableOrder(Exception):
    pass


def read_pdf_text(pdf_path):
    from pypdf import PdfReader

    path = Path(pdf_path)
    if not path.is_file():
        raise UnreadableOrder(f"no tariff order at {path}")
    try:
        pages = [page.extract_text() or "" for page in PdfReader(str(path)).pages]
    except Exception as error:
        raise UnreadableOrder(f"the tariff order at {path} cannot be read: {error}") from error
    text = "\n".join(pages)
    if not text.strip():
        raise UnreadableOrder(f"the tariff order at {path} yields no text")
    return text


def read_manifest(manifest_path=constants.TARIFF_ORDERS_MANIFEST_PATH):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if isinstance(manifest, dict):
        for key in ("orders", "tariff_orders"):
            if isinstance(manifest.get(key), list):
                return manifest[key]
    return manifest


def _document_name(entry):
    for candidate in DOCUMENT_NAME_CANDIDATES:
        if entry.get(candidate):
            return entry[candidate]
    return f"{entry['order_id']}.pdf"


def _section_headings(entry, text):
    for candidate in SECTION_CANDIDATES:
        if entry.get(candidate):
            return list(entry[candidate])
    return [heading.strip() for heading in HEADING_LINE_PATTERN.findall(text)]


def load_tariff_orders(orders_directory=constants.TARIFF_ORDERS_DIRECTORY,
                       manifest_path=constants.TARIFF_ORDERS_MANIFEST_PATH):
    orders = []
    for entry in read_manifest(manifest_path):
        text = read_pdf_text(Path(orders_directory) / Path(_document_name(entry)).name)
        order = dict(entry)
        order["order_id"] = entry.get("order_id", entry.get("id"))
        for field in ("title", "consumer_category", "effective_from", "effective_to"):
            order.setdefault(field, None)
        order["sections"] = _section_headings(entry, text)
        order["text"] = text
        orders.append(order)
    return orders


if __name__ == "__main__":
    loaded = load_tariff_orders()
    characters = sum(len(order["text"]) for order in loaded)
    print(f"{len(loaded)} orders, {characters} characters of text")
