import os
import uuid
import logging
import chromadb
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import SimpleDirectoryReader
from assignments.Assignment3.core.config import settings

# --- Setup Logging ---
# In production, this allows you to track issues in the Docker logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self):
        try:
            logger.info("Initializing RAGManager components...")
            
            # 1. Load Embedding Model
            # This is heavy, so we log the start and finish
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")

            # 2. Connect to ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST, 
                port=settings.CHROMA_PORT
            )
            
            # 3. Access Collection
            self.collection = self.chroma_client.get_or_create_collection(name="maven_docs")
            logger.info(f"Connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")

            # 4. Text Splitter configuration
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize RAGManager: {str(e)}")
            raise RuntimeError("AI Engine initialization failed.") from e

    def process_and_store(self, file_path: str) -> int:
        """
        Extracts text, chunks it, converts to vectors, and stores in ChromaDB.
        """
        try:
            logger.info(f"Starting processing for file: {file_path}")

            # Step 1: Extraction
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at {file_path}")

            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            full_text = " ".join([doc.text for doc in documents])
            
            if not full_text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return 0

            # Step 2: Chunking
            chunks = self.text_splitter.split_text(full_text)
            logger.info(f"Created {len(chunks)} chunks from {file_path}")

            # Step 3: Embedding (Mathematical conversion)
            embeddings = self.model.encode(chunks).tolist()

            # Step 4: Storage
            ids = [str(uuid.uuid4()) for _ in chunks]
            self.collection.add(
                ids=ids, 
                embeddings=embeddings, 
                documents=chunks
            )
            
            logger.info(f"Successfully stored {len(chunks)} vectors in ChromaDB.")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error in process_and_store for {file_path}: {str(e)}")
            # Re-raise to let the API route handle the HTTP response
            raise

    def get_context(self, query: str, n_results: int = 3) -> str:
        """
        Retrieves the most relevant text chunks based on the user query.
        """
        try:
            logger.info(f"Querying ChromaDB for context: '{query[:50]}...'")

            # 1. Convert query to vector
            query_embedding = self.model.encode([query]).tolist()
            
            # 2. Similarity Search
            results = self.collection.query(
                query_embeddings=query_embedding, 
                n_results=n_results
            )

            if not results['documents'] or not results['documents'][0]:
                logger.warning("No relevant context found in Vector DB.")
                return ""

            context = "\n---\n".join(results['documents'][0])
            logger.info("Successfully retrieved context from ChromaDB.")
            return context

        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {str(e)}")
            return "" # Return empty string so Gemini can still try to answer if possible