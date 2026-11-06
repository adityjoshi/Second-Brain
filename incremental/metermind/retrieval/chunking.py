import json
from pathlib import Path

from config import constants
from metermind.retrieval.document_loader import load_tariff_orders

CHUNK_FIELDS = ("chunk_id", "text") + tuple(constants.STORED_CHUNK_FIELDS)


def split_into_chunks(text, size=constants.CHUNK_CHARACTERS,
                      overlap=constants.CHUNK_OVERLAP_CHARACTERS):
    if overlap >= size:
        raise ValueError(
            f"an overlap of {overlap} is not smaller than a piece of {size}, "
            f"so the cut would never advance"
        )
    step = size - overlap
    pieces = []
    start = 0
    while start < len(text):
        piece = text[start : start + size]
        if piece.strip():
            pieces.append(piece)
        if start + size >= len(text):
            break
        start += step
    return pieces


def _heading_in(order, chunk_text):
    lowered = chunk_text.lower()
    found = [
        (lowered.find(heading.lower()), heading)
        for heading in order.get("sections") or []
        if heading and heading.lower() in lowered
    ]
    return min(found)[1] if found else ""


def chunk_metadata(order, chunk_text, position):
    return {
        "chunk_id": f"{order['order_id']}-{position:03d}",
        "text": chunk_text,
        "order_id": order["order_id"],
        "title": order.get("title"),
        "consumer_category": order.get("consumer_category"),
        "effective_from": order.get("effective_from"),
        "effective_to": order.get("effective_to"),
        "section": _heading_in(order, chunk_text),
    }


def write_chunks(orders, chunks_path=constants.TARIFF_CHUNKS_PATH):
    chunks = []
    seen = set()
    for order in orders:
        carried = ""
        for position, piece in enumerate(split_into_chunks(order["text"])):
            chunk = chunk_metadata(order, piece, position)
            if chunk["chunk_id"] in seen:
                raise ValueError(f"two pieces share the identifier {chunk['chunk_id']}")
            seen.add(chunk["chunk_id"])
            if not chunk["section"]:
                chunk["section"] = carried
            carried = chunk["section"]
            chunks.append({field: chunk[field] for field in CHUNK_FIELDS})

    path = Path(chunks_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "orders": len(orders),
        "chunks": len(chunks),
        "without_a_section": sum(1 for chunk in chunks if not chunk["section"]),
    }


if __name__ == "__main__":
    print(write_chunks(load_tariff_orders()))
