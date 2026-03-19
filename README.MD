# Maven AI Engineering Backend

A collection of production-grade AI systems demonstrating scalable, secure, and efficient architectures for LLM-based applications.

This repository serves as a modular AI engineering workspace. Each project is designed to solve specific real-world problems while experimenting with distinct architectural patterns to optimize performance, cost, and reliability.

---

## 🚀 Core Features

* **Retrieval-Augmented Generation (RAG):** Advanced document chunking and vector database integration.
* **DAG-based Execution Pipelines:** Structured, non-linear task orchestration for complex logic.
* **Multi-Agent Architectures:** Specialized agents collaborating to solve multifaceted tasks.
* **Hybrid Routing:** Rule-based logic combined with LLM fallback for optimal cost-efficiency.
* **LLM-as-a-Judge Evaluation:** Automated systems for tracking metrics like Correctness and Faithfulness.
* **Prompt Injection Defense:** Multi-layered security (Regex + Sandwich Pattern) to prevent malicious overrides.
* **AST-based Safe Tool Execution:** Secure evaluation of Python expressions to prevent arbitrary code execution.
* **Parallel & Async Execution:** Optimized for high-concurrency and low-latency workloads.

---

## 🏗 System Architecture

The system is designed using a service-oriented architecture to ensure modularity and scalability:

**User Request** ↓  
**Hybrid Router** (Keyword-based O(1) classification + LLM fallback)  
↓  
**Core Logic** (Agentic QA / RAG Pipeline / DAG Workflow)  
↓  
**Tool Execution Layer** (Safe AST-based Sandbox)  
↓  
**Evaluation Layer** (LLM-as-a-Judge for Response Verification)  
↓  
**Final Response**

---

## 🛠 Tech Stack

| Category | Tools & Frameworks |
| :--- | :--- |
| **AI Frameworks** | LangChain, LangGraph, LlamaIndex, OpenAI, Groq, Google GenAI |
| **NLP & ML** | HuggingFace Transformers, Sentence Transformers, PyTorch, Scikit-learn |
| **Vector Databases** | ChromaDB, Qdrant, FAISS |
| **Backend & API** | FastAPI, Flask, Uvicorn, Redis |
| **Data Handling** | Pandas, NumPy |
| **Infrastructure** | Docker, Docker Compose, PostgreSQL, MongoDB |
| **UI & Viz** | Streamlit, Gradio, Plotly |

---

## 📂 Repository Structure

The projects are fully isolated within the `assignments/` directory, allowing them to be run independently.

```text
/assignments/
├── AgenticQASystem/   # Intelligent QA with agentic reasoning
├── MultiAgents/       # Collaborative multi-agent workflows
├── RAG/               # Advanced Retrieval-Augmented Generation
├── Evaluation/        # LLM-as-a-Judge and metric tracking systems
└── Tools/             # Safe tool execution and utility modules

Key Innovations & Performance
1. Hybrid Routing System
Optimization: Uses keyword-based classification for common queries to bypass LLM calls.

Impact: Reduces LLM API costs by 70–80%.

Speed: Improves system latency from ~500ms to ~50ms for routed queries.

2. Security-First Design
Prompt Injection Defense: Utilizes delimiter-based isolation (Sandwich Pattern) and regex-based detection to sanitize inputs.

AST Safety: Evaluates expressions via Python's Abstract Syntax Tree, allowing strict operator-level control and preventing arbitrary code execution.

3. LLM-as-a-Judge Evaluation
Metrics tracked: Correctness, Faithfulness, Helpfulness, Context Recall, and Precision.

Reliability: Implements automated retries, timeouts, and structured JSON parsing.

⚙️ Setup & Installation
Docker Setup (Recommended)
This command starts the FastAPI backend, Streamlit UI, Jupyter Lab, and all vector databases.
docker-compose up --build
Service Access:

FastAPI Backend: http://localhost:8000

Streamlit UI: http://localhost:8501

Jupyter Lab: http://localhost:8888

Vector DBs: ChromaDB (8001), Qdrant (6333)

Local Setup
Install Requirements:

Bash

pip install -r requirements.txt
Environment Variables: Create a .env file:

Code snippet

GROQ_API_KEY=your_key
GOOGLE_API_KEY=your_key
LLAMA_API_KEY=your_key
Run Services:

Bash

# Run Backend
uvicorn assignments.main:app --reload

# Run UI
streamlit run assignments/streamlit_app.py
👨‍💻 Author
Shayan Kashif

Focus: AI Systems, LLM Optimization, Backend Architecture

GitHub: shayankashif123

Experience: Full Stack Developer with a focus on AI Engineering and Security.