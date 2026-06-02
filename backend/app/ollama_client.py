from __future__ import annotations

from typing import List

import requests


def _embed_batch(host: str, model: str, texts: List[str], timeout: int) -> List[List[float]]:
    """Embed one batch of texts using the best Ollama endpoint available."""
    base_host = host.rstrip("/")

    embed_response = requests.post(
        f"{base_host}/api/embed",
        json={"model": model, "input": texts},
        timeout=timeout,
    )

    if embed_response.ok:
        payload = embed_response.json()
        embeddings = payload.get("embeddings")
        if isinstance(embeddings, list) and embeddings:
            return embeddings
        raise RuntimeError("Ollama /api/embed returned an unexpected response format.")

    if embed_response.status_code != 404:
        embed_response.raise_for_status()

    result: List[List[float]] = []
    for text in texts:
        single_response = requests.post(
            f"{base_host}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=timeout,
        )
        single_response.raise_for_status()

        payload = single_response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("Ollama /api/embeddings returned an unexpected response format.")
        result.append(embedding)

    return result


def get_embeddings(host: str, model: str, texts: List[str], timeout: int = 300, batch_size: int = 16) -> List[List[float]]:
    """Return embeddings for input texts, supporting old and new Ollama APIs.

    Newer Ollama versions support batched requests at /api/embed with {"input": [...]}
    while older versions expose /api/embeddings with {"prompt": "..."} one-by-one.
    """
    if not texts:
        return []

    effective_batch_size = max(1, batch_size)
    result: List[List[float]] = []
    for start_index in range(0, len(texts), effective_batch_size):
        batch = texts[start_index:start_index + effective_batch_size]
        result.extend(_embed_batch(host, model, batch, timeout))

    return result
