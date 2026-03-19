import asyncio
import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Sequence

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import SimpleDirectoryReader
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def format_docs(docs: Sequence[Document]) -> str:
    return "\n---\n".join([doc.page_content for doc in docs])


class SyntheticRAGManager:
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    DOCS_COLLECTION_NAME = "synthetic5_docs"
    EVAL_COLLECTION_NAME = "synthetic5_eval"

    EMBED_BATCH_SIZE = 32
    UPSERT_BATCH_SIZE = 128
    MAX_EMBED_CONCURRENCY = 2
    MAX_LLM_CONCURRENCY = 4
    MAX_RETRIES = 3
    LLM_TIMEOUT_SEC = 60
    QUERY_BACKOFF_BASE_SEC = 1.5
    QUERY_MAX_RETRIES = 3

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        default_k: int = 2,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_k = default_k

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=self.EMBEDDING_MODEL)

        self.qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        self.async_qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        self.embedding_size = len(self.embeddings.embed_query("embedding_size_probe"))
        self._ensure_collection(self.DOCS_COLLECTION_NAME)
        self._ensure_collection(self.EVAL_COLLECTION_NAME)

        self.llm = get_llm()
        self.synthetic_prompt = ChatPromptTemplate.from_template(
            """You are creating a synthetic evaluation dataset for a RAG system.
Generate {num_questions} high-quality QA records from the context.

Rules:
1) Use only facts from context.
2) Return strict JSON, no markdown.
3) JSON schema:
[
  {{
    "question": "...",
    "reference_answer": "...",
    "reference_context": "..."
  }}
]

Context:
{context}
"""
        )
        self.answer_prompt = ChatPromptTemplate.from_template(
            """Answer the question using ONLY the provided context.
If context is insufficient respond exactly:
"I don't have enough information."

Context:
{context}

Question: {question}
"""
        )

    async def process_generate_and_store_evalset(
        self,
        file_path: str,
        total_questions: int = 12,
    ) -> Dict[str, int]:
        """
        Non-blocking fan-out:
        - Branch A: chunk embed + docs upsert
        - Branch B: synthetic QA generation + eval upsert
        """
        full_text = await asyncio.to_thread(self._extract_text, file_path=file_path)
        if not full_text:
            return {"indexed_chunks": 0, "generated_qas": 0}

        chunks = await asyncio.to_thread(self.text_splitter.split_text, full_text)
        source_file = os.path.basename(file_path)

        index_task = asyncio.create_task(
            self._embed_and_store_document_chunks_async(chunks=chunks, source_file=source_file)
        )
        synth_task = asyncio.create_task(
            self._generate_and_store_synthetic_evalset_async(
                chunks=chunks,
                total_questions=total_questions,
                source_file=source_file,
            )
        )
        indexed_chunks, generated_qas = await asyncio.gather(index_task, synth_task)
        return {"indexed_chunks": indexed_chunks, "generated_qas": generated_qas}

    async def fetch_eval_records(
        self,
        source_file: str = "",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        query_filter = None
        if source_file:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source_file",
                        match=MatchValue(value=source_file),
                    )
                ]
            )

        points, _ = await self.async_qdrant_client.scroll(
            collection_name=self.EVAL_COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        records: List[Dict[str, Any]] = []
        for point in points:
            payload = point.payload or {}
            records.append(
                {
                    "id": str(point.id),
                    "question": payload.get("question", ""),
                    "reference_answer": payload.get("reference_answer", ""),
                    "reference_context": payload.get("reference_context", ""),
                    "source_file": payload.get("source_file", ""),
                }
            )
        return records

    async def search_documents(self, question: str, k: int = 5) -> List[Document]:
        query_vector = await asyncio.to_thread(self.embeddings.embed_query, question)
        hits = await self.async_qdrant_client.search(
            collection_name=self.DOCS_COLLECTION_NAME,
            query_vector=query_vector,
            limit=k,
            with_payload=True,
        )
        docs: List[Document] = []
        for hit in hits:
            payload = hit.payload or {}
            docs.append(
                Document(
                    page_content=payload.get("text", ""),
                    metadata={
                        "source_file": payload.get("source_file", "unknown"),
                        "score": hit.score,
                    },
                )
            )
        return docs

    async def aquery(self, question: str) -> Dict[str, str]:
        docs = await self.search_documents(question=question, k=self.default_k)
        context = format_docs(docs)
        prompt_messages = self.answer_prompt.format_messages(
            context=context,
            question=question,
        )
        response = None
        for attempt in range(1, self.QUERY_MAX_RETRIES + 1):
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(prompt_messages),
                    timeout=self.LLM_TIMEOUT_SEC,
                )
                break
            except Exception as exc:
                if attempt == self.QUERY_MAX_RETRIES:
                    raise
                await asyncio.sleep(self._compute_backoff_delay(exc, attempt))
        if response is None:
            raise RuntimeError("LLM query failed after retries.")
        return {
            "answer": response.content,
            "sources": context,
        }

    def _extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError("Upload file missing")

        docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
        text = " ".join([doc.text for doc in docs])
        if not text.strip():
            return ""
        return text

    def _ensure_collection(self, collection_name: str) -> None:
        existing = [col.name for col in self.qdrant_client.get_collections().collections]
        if collection_name in existing:
            return
        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=self.embedding_size, distance=Distance.COSINE),
        )

    async def _embed_and_store_document_chunks_async(
        self,
        chunks: List[str],
        source_file: str,
    ) -> int:
        if not chunks:
            return 0

        semaphore = asyncio.Semaphore(self.MAX_EMBED_CONCURRENCY)
        tasks = [
            asyncio.create_task(
                self._embed_doc_batch_and_store(
                    chunk_batch=batch,
                    source_file=source_file,
                    semaphore=semaphore,
                )
            )
            for batch in self._batched(chunks, self.EMBED_BATCH_SIZE)
        ]
        if tasks:
            await asyncio.gather(*tasks)
        return len(chunks)

    async def _embed_doc_batch_and_store(
        self,
        chunk_batch: Sequence[str],
        source_file: str,
        semaphore: asyncio.Semaphore,
    ) -> None:
        async with semaphore:
            vectors = await asyncio.to_thread(self.embeddings.embed_documents, list(chunk_batch))
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vectors[idx],
                    payload={
                        "text": chunk,
                        "source_file": source_file,
                        "record_type": "doc_chunk",
                    },
                )
                for idx, chunk in enumerate(chunk_batch)
            ]
            await self._upsert_points_with_retry(self.DOCS_COLLECTION_NAME, points)

    async def _generate_and_store_synthetic_evalset_async(
        self,
        chunks: List[str],
        total_questions: int,
        source_file: str,
    ) -> int:
        if not chunks or total_questions <= 0:
            return 0

        selected_chunks = chunks[: min(len(chunks), max(1, total_questions))]
        per_chunk = max(1, total_questions // len(selected_chunks))
        remainder = total_questions % len(selected_chunks)

        semaphore = asyncio.Semaphore(self.MAX_LLM_CONCURRENCY)
        tasks = []
        for idx, chunk in enumerate(selected_chunks):
            num_questions = per_chunk + (1 if idx < remainder else 0)
            tasks.append(
                asyncio.create_task(
                    self._generate_for_chunk(
                        chunk=chunk,
                        num_questions=num_questions,
                        semaphore=semaphore,
                    )
                )
            )

        generated_sets = await asyncio.gather(*tasks, return_exceptions=True)
        records: List[Dict[str, str]] = []
        for generated in generated_sets:
            if isinstance(generated, Exception):
                logger.exception("Synthetic generation worker failed: %s", generated)
                continue
            records.extend(generated)

        records = records[:total_questions]
        if records:
            await self._store_synthetic_evalset_async(records, source_file)
        return len(records)

    async def _generate_for_chunk(
        self,
        chunk: str,
        num_questions: int,
        semaphore: asyncio.Semaphore,
    ) -> List[Dict[str, str]]:
        async with semaphore:
            prompt_messages = self.synthetic_prompt.format_messages(
                context=chunk,
                num_questions=num_questions,
            )
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    response = await asyncio.wait_for(
                        self.llm.ainvoke(prompt_messages),
                        timeout=self.LLM_TIMEOUT_SEC,
                    )
                    return self._parse_json_records(response.content.strip())
                except Exception as exc:
                    if attempt == self.MAX_RETRIES:
                        logger.warning("LLM generation failed after retries: %s", exc)
                        return []
                    await asyncio.sleep(min(4, 2 ** (attempt - 1)))
        return []

    async def _store_synthetic_evalset_async(
        self,
        dataset: List[Dict[str, str]],
        source_file: str,
    ) -> None:
        for batch in self._batched(dataset, self.EMBED_BATCH_SIZE):
            question_vectors = await asyncio.to_thread(
                self.embeddings.embed_documents,
                [item["question"] for item in batch],
            )
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=question_vectors[idx],
                    payload={
                        "question": item["question"],
                        "reference_answer": item["reference_answer"],
                        "reference_context": item["reference_context"],
                        "source_file": source_file,
                        "record_type": "synthetic_eval",
                    },
                )
                for idx, item in enumerate(batch)
            ]
            await self._upsert_points_with_retry(self.EVAL_COLLECTION_NAME, points)

    async def _upsert_points_with_retry(
        self,
        collection_name: str,
        points: List[PointStruct],
    ) -> None:
        if not points:
            return

        for idx in range(0, len(points), self.UPSERT_BATCH_SIZE):
            chunk = points[idx : idx + self.UPSERT_BATCH_SIZE]
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    await self.async_qdrant_client.upsert(
                        collection_name=collection_name,
                        points=chunk,
                        wait=True,
                    )
                    break
                except Exception as exc:
                    if attempt == self.MAX_RETRIES:
                        raise RuntimeError(
                            f"Failed upsert for collection={collection_name}"
                        ) from exc
                    await asyncio.sleep(min(4, 2 ** (attempt - 1)))

    def _parse_json_records(self, model_output: str) -> List[Dict[str, str]]:
        cleaned = model_output.replace("```json", "").replace("```", "").strip()
        try:
            raw_items = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Synthetic generation output is not valid JSON.")
            return []

        if not isinstance(raw_items, list):
            return []

        records: List[Dict[str, str]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            question = item.get("question", "").strip()
            answer = item.get("reference_answer", "").strip()
            context = item.get("reference_context", "").strip()
            if question and answer and context:
                records.append(
                    {
                        "question": question,
                        "reference_answer": answer,
                        "reference_context": context,
                    }
                )
        return records

    @staticmethod
    def _compute_backoff_delay(exc: Exception, attempt: int) -> float:
        """
        Exponential backoff with optional retry-after parsing from error message.
        """
        message = str(exc)
        match = re.search(r"try again in ([0-9.]+)s", message, re.IGNORECASE)
        if match:
            return max(0.5, float(match.group(1)))
        return min(8.0, SyntheticRAGManager.QUERY_BACKOFF_BASE_SEC ** attempt)

    def _batched(self, items: Sequence[Any], batch_size: int) -> List[List[Any]]:
        return [list(items[idx : idx + batch_size]) for idx in range(0, len(items), batch_size)]
