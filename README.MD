Maven AI Engineering Backend

A collection of production-grade AI systems demonstrating scalable, secure, and efficient architectures for LLM-based applications.

This repository contains multiple independent projects exploring modern AI engineering patterns such as RAG pipelines, multi-agent systems, DAG-based workflows, hybrid routing, and security-focused AI design.

Overview

This repository serves as a modular AI engineering workspace, where each project is designed to:

Solve a specific real-world problem

Experiment with a distinct architectural pattern

Optimize performance, cost, and reliability

Each project is:

Fully isolated in its own directory

Independently runnable

Built with the most suitable tools for its use case

Core Features

Retrieval-Augmented Generation (RAG)

DAG-based Execution Pipelines

Multi-Agent Architectures

Hybrid Routing (Rule-based + LLM fallback)

LLM-as-a-Judge Evaluation Systems

Prompt Injection Defense

AST-based Safe Tool Execution

Parallel and Async Execution

System Architecture

The system is designed using a service-oriented architecture:

User Request
     ↓
Hybrid Router (Rule-based + LLM fallback)
     ↓
Agent / RAG / DAG System
     ↓
Tool Execution Layer (Safe AST Execution)
     ↓
Evaluation Layer (LLM-as-Judge)
     ↓
Response
Tech Stack
AI & LLM Frameworks

LangChain, LangGraph

LlamaIndex

OpenAI, Groq, Google GenAI

NLP & Transformers

HuggingFace Transformers

Sentence Transformers

Vector Databases

ChromaDB

Qdrant

FAISS

Backend & APIs

FastAPI

Flask

Uvicorn

Data & ML

PyTorch, TensorFlow

Scikit-learn

Pandas, NumPy

Infrastructure

Docker, Docker Compose

Redis

PostgreSQL / MongoDB

Visualization & UI

Streamlit

Gradio

Plotly

Repository Structure
/assignments/
├── AgenticQASystem/
├── MultiAgents/
├── RAG/
├── Evaluation/
├── Tools/

Each folder contains a standalone implementation.

Key Innovations
Hybrid Routing System

O(1) keyword-based classification

LLM fallback for ambiguity

Reduces LLM calls by 70–80%

Improves latency from ~500ms → ~50ms

Prompt Injection Defense

Regex-based detection

Delimiter-based prompt isolation (Sandwich Pattern)

Protection against direct & indirect injection

AST-Based Tool Safety

Safe evaluation of expressions using Python AST

Prevents arbitrary code execution

Strict operator-level control

LLM-as-a-Judge Evaluation

Metrics: Correctness, Faithfulness, Helpfulness, Context Recall & Precision

Includes retry, timeout, and structured parsing

Parallel Execution

Async pipelines

Optimized for concurrent workloads

Docker-Based Setup (Recommended)
Start All Services
docker-compose up --build

Services included:

FastAPI → Backend API (localhost:8000)

Streamlit → UI (localhost:8501)

Jupyter Lab → Development (localhost:8888)

ChromaDB → Vector DB

Qdrant → Vector DB

Ports:

Service	Port
FastAPI	8000
Streamlit	8501
Jupyter	8888
ChromaDB	8001
Qdrant	6333

Environment Variables:

Create a .env file:

GROQ_API_KEY=your_key
GOOGLE_API_KEY=your_key
LLAMA_API_KEY=your_key
Local Setup (Without Docker)
pip install -r requirements.txt

Run FastAPI:

uvicorn assignments.main:app --reload

Run Streamlit:

streamlit run assignments/streamlit_app.py
Example Use Cases

AI-powered content generation systems

Research pipelines using RAG

Multi-agent orchestration systems

Secure tool execution environments

Evaluation pipelines for LLM outputs

Security Design

Prompt injection detection

Input sanitization

Safe tool execution via AST

Controlled LLM interaction

Performance Highlights

70–80% reduction in LLM calls

Low latency (~50ms for common queries)

Efficient concurrent execution

Author

Shayan Kashif

GitHub: https://github.com/shayankashif123

Focus: AI Systems, LLM Optimization, Backend Architecture