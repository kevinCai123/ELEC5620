from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:  # pragma: no cover
    OpenAIEmbeddings = None  # type: ignore

from app.core.config import get_settings


DEFAULT_INDEX_PATH = Path(".ai_index")


def _embeddings():
    settings = get_settings()
    api_key = settings.openai_api_key
    if OpenAIEmbeddings is None:
        logger = __import__("logging").getLogger(__name__)
        logger.info("langchain-openai not installed; falling back to local embeddings model")
    if api_key and OpenAIEmbeddings is not None:
        model = settings.openai_embed_model
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        embeddings = OpenAIEmbeddings(model=model, api_key=api_key)
        logger = __import__("logging").getLogger(__name__)
        logger.info("Using OpenAI embeddings", extra={"model": model})
        return embeddings
    model_name = settings.local_embeddings_model or "sentence-transformers/all-MiniLM-L6-v2"
    return HuggingFaceEmbeddings(model_name=model_name)


def ingest_folder(folder: str, index_path: Path | None = None) -> None:
    target = index_path or DEFAULT_INDEX_PATH
    target.mkdir(parents=True, exist_ok=True)

    base_path = Path(folder)
    if not base_path.exists():
        msg = f"Ingest folder {folder} does not exist"
        raise FileNotFoundError(msg)

    docs: list[Document] = []
    for path in base_path.rglob("*"):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        content = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=content, metadata={"source": str(path)}))

    if not docs:
        msg = f"No documents found in {folder}"
        raise ValueError(msg)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=200)
    split_docs = splitter.split_documents(docs)
    embeddings = _embeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    vectorstore.save_local(str(target))
    meta = {
        "documents": len(docs),
        "chunks": len(split_docs),
        "sources": sorted({doc.metadata.get("source") for doc in split_docs}),
    }
    (target / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def get_retriever(top_k: int = 5, index_path: Path | None = None) -> Callable[[str], List[Document]] | None:
    target = index_path or DEFAULT_INDEX_PATH
    if not target.exists():
        return None

    embeddings = _embeddings()
    try:
        vectorstore = FAISS.load_local(
            str(target), embeddings, allow_dangerous_deserialization=True
        )
    except Exception:  # pragma: no cover - corrupted index
        return None

    def retrieve(query: str) -> List[Document]:
        return vectorstore.similarity_search(query, k=top_k)

    return retrieve


__all__ = ["ingest_folder", "get_retriever"]
