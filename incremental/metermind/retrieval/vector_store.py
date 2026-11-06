import json
import logging
from pathlib import Path

import numpy as np

from config import constants

STORE_SETTINGS = {"hnsw:space": constants.VECTOR_DISTANCE_MEASURE}
SEARCH_RESULT_FIELDS = ("chunk_id", "text", "distance") + tuple(constants.STORED_CHUNK_FIELDS)
DEMONSTRATION_QUESTION = "What is the fixed charge on a domestic connection?"


class TariffStoreMissing(Exception):
    pass


def load_embedder(model_name=constants.EMBEDDING_MODEL_NAME):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _embed(embedder, texts):
    return np.asarray(embedder.encode(list(texts)), dtype=float).tolist()


def _stored_metadata(chunk):
    # The store refuses empty values, so a missing field is kept as empty text.
    return {
        field: ("" if chunk.get(field) is None else chunk[field])
        for field in constants.STORED_CHUNK_FIELDS
    }


def _store_client(store_directory):
    import chromadb
    from chromadb.config import Settings

    logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
    return chromadb.PersistentClient(
        path=str(store_directory), settings=Settings(anonymized_telemetry=False)
    )


def build_tariff_store(chunks_path=constants.TARIFF_CHUNKS_PATH,
                       store_directory=constants.TARIFF_STORE_DIRECTORY, embedder=None):
    chunks = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
    if embedder is None:
        embedder = load_embedder()
    Path(store_directory).mkdir(parents=True, exist_ok=True)
    client = _store_client(store_directory)
    try:
        client.delete_collection(constants.TARIFF_STORE_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=constants.TARIFF_STORE_COLLECTION, metadata=dict(STORE_SETTINGS)
    )
    if chunks:
        collection.add(
            ids=[chunk["chunk_id"] for chunk in chunks],
            documents=[chunk["text"] for chunk in chunks],
            embeddings=_embed(embedder, [chunk["text"] for chunk in chunks]),
            metadatas=[_stored_metadata(chunk) for chunk in chunks],
        )
    return collection


def open_tariff_store(store_directory=constants.TARIFF_STORE_DIRECTORY):
    if not Path(store_directory).is_dir():
        raise TariffStoreMissing(f"no tariff store has been built at {store_directory}")
    client = _store_client(store_directory)
    try:
        return client.get_collection(constants.TARIFF_STORE_COLLECTION)
    except Exception as error:
        raise TariffStoreMissing(
            f"the store at {store_directory} holds no collection named "
            f"{constants.TARIFF_STORE_COLLECTION}"
        ) from error


def _results(found):
    results = []
    for chunk_id, text, distance, metadata in zip(
        found["ids"][0], found["documents"][0], found["distances"][0], found["metadatas"][0]
    ):
        result = {"chunk_id": chunk_id, "text": text, "distance": float(distance)}
        for field in constants.STORED_CHUNK_FIELDS:
            result[field] = (metadata or {}).get(field, "")
        results.append(result)
    return sorted(results, key=lambda result: result["distance"])


def _store_condition(conditions):
    clauses = [{field: value} for field, value in sorted(conditions.items())]
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def search_with_filter(collection, question, embedder, conditions,
                       result_count=constants.SEARCH_RESULT_COUNT):
    stored = collection.count()
    if stored == 0:
        return []
    asked = {
        "query_embeddings": _embed(embedder, [question]),
        "n_results": min(result_count, stored),
        "include": ["documents", "metadatas", "distances"],
    }
    if conditions:
        asked["where"] = _store_condition(conditions)
    return _results(collection.query(**asked))


def search_tariff(collection, question, embedder, result_count=constants.SEARCH_RESULT_COUNT):
    return search_with_filter(collection, question, embedder, None, result_count)


if __name__ == "__main__":
    embedder = load_embedder()
    collection = build_tariff_store(embedder=embedder)
    print(f"{collection.count()} chunks stored")
    for result in search_tariff(collection, DEMONSTRATION_QUESTION, embedder):
        print(f"  {result['distance']:.3f}  {result['order_id']:<16}  {result['section']}")
