import os
import uuid
import logging
import chromadb
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import SimpleDirectoryReader

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from assignments.Assignment3.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def format_docs(docs: List[Any]) -> str:
    """
    Converts retrieved LangChain documents into a single formatted context string.
    """
    return "\n---\n".join([doc.page_content for doc in docs])



class RAGManager:
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = "maven_docs"

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        default_k: int = 10,
    ):
        logger.info("Initializing RAGManager components...")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_k = default_k

        # Text chunking component
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        # Low level ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )

        # Ensure collection exists
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.COLLECTION_NAME
        )

        # Single embedding system for ingest + query
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.EMBEDDING_MODEL
        )

        # High level vectorstore wrapper
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=self.COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

        # Build LCEL query chain
        self.lcel_chain = self._build_query_chain()

    # -------- Ingestion Pipeline (procedural) --------

    def process_and_store(self, file_path: str) -> int:
        """
        Extracts text, chunks it, embeds it, and stores vectors in ChromaDB.
        """
        logger.info(f"Starting ingestion for file: {file_path}")

        full_text = self._extract_text(file_path)

        if not full_text:
            return 0

        chunks = self.text_splitter.split_text(full_text)
        embeddings = self.embeddings.embed_documents(chunks)

        ids = [str(uuid.uuid4()) for _ in chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
        )

        logger.info(f"Indexed {len(chunks)} chunks.")
        return len(chunks)

    def _extract_text(self, file_path: str) -> str:
        """
        Reads and extracts raw text from uploaded file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError("Upload file missing")

        docs = SimpleDirectoryReader(input_files=[file_path]).load_data()

        text = " ".join([d.text for d in docs])

        if not text.strip():
            logger.warning("No text extracted.")
            return ""

        return text

    def _build_query_chain(self):
        """
        Builds a production LCEL chain with parallel components.
        """

        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.default_k}
        )

        llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            api_key=settings.GOOGLE_API_KEY,
        )
        prompt = ChatPromptTemplate.from_template("""Answer the question using ONLY the provided context.
If context is insufficient respond exactly:

"I don't have enough information."

Context:
{context}

Question: {question}""")



        # Parallel execution: retrieval + question passthrough
        parallel_inputs = RunnableParallel(
            context=retriever,
            question=RunnablePassthrough(),
        )

        # Transform outputs and run final chain
        return (
            parallel_inputs
            | {
                "context": lambda x: format_docs(x["context"]),
                "question": lambda x: x["question"],
            }
            | prompt
            | llm
        )

    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Synchronous production query.
        Sources are retrieved consistently using same k value.
        """
        logger.info("Running LCEL query chain...")
        response = self.lcel_chain.invoke(question)

        docs = self.vectorstore.similarity_search(
            question, k=self.default_k
        )

        return {
            "answer": response.content,
            "sources": format_docs(docs),
        }

    async def aquery(self, question: str) -> Dict[str, Any]:
        """
        Async parallel query interface.
        """
        logger.info(f"Running async LCEL query: {question[:50]}...")
        response = await self.lcel_chain.ainvoke(question)

        docs = await self.vectorstore.asimilarity_search(
            question, k=self.default_k
        )

        return {
            "answer": response.content,
            "sources": format_docs(docs),
        }
