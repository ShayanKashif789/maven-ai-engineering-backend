import asyncio
import json
import logging
import re
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate

from assignments.AgenticQASystem3.core.llm_factory import get_llm

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    Production-grade LLM-as-a-judge evaluator.
    Evaluates correctness, faithfulness, and helpfulness.
    """

    MAX_RETRIES = 3
    LLM_TIMEOUT_SEC = 60
    BACKOFF_BASE_SEC = 1.5

    def __init__(self) -> None:
        self.llm = get_llm()

        self.eval_prompt = ChatPromptTemplate.from_template(
            """
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.

Evaluate the model answer and retrieval quality.

Metrics:

Correctness
Does the model answer match the reference answer factually?

Faithfulness
Is the model answer supported by the retrieved context? Penalize hallucinations.

Helpfulness
Is the answer clear, useful, and well explained?

Context Recall
Does the retrieved context contain the information required to answer the question according to the reference context?

Context Precision
How relevant and focused is the retrieved context to the question?

Scoring Guide:
0 = completely incorrect
5 = perfect

Question:
{question}

Reference Answer:
{reference_answer}

Reference Context:
{reference_context}

Retrieved Context:
{retrieved_context}

Model Answer:
{rag_answer}

Return STRICT JSON ONLY:

{{
  "correctness": integer,
  "faithfulness": integer,
  "helpfulness": integer,
  "context_recall": integer,
  "context_precision": integer,
  "reasoning": "short explanation"
}}
"""
        )

    async def evaluate(
        self,
        question: str,
        reference_answer: str,
        reference_context: str,
        retrieved_context: str,
        rag_answer: str,
    ) -> Dict[str, Any]:
        """
        Run evaluation using LLM-as-a-judge.

        Returns structured evaluation scores.
        """

        prompt_messages = self.eval_prompt.format_messages(
            question=question,
            reference_answer=reference_answer,
            reference_context=reference_context,
            retrieved_context=retrieved_context,
            rag_answer=rag_answer,
        )

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(prompt_messages),
                    timeout=self.LLM_TIMEOUT_SEC,
                )

                return self._parse_evaluation_json(response.content)

            except Exception as exc:
                logger.warning(
                    "Evaluator attempt %s failed: %s", attempt, str(exc)
                )

                if attempt == self.MAX_RETRIES:
                    return {
                        "correctness": 0,
                        "faithfulness": 0,
                        "helpfulness": 0,
                        "context_recall": 0,
                        "context_precision": 0,
                        "reasoning": "Evaluation failed after retries.",
                    }

                await asyncio.sleep(self._compute_backoff_delay(exc, attempt))

        return {
            "correctness": 0,
            "faithfulness": 0,
            "helpfulness": 0,
            "context_recall": 0,
            "context_precision": 0,
            "reasoning": "Evaluation fallback.",
        }

    @staticmethod
    def _compute_backoff_delay(exc: Exception, attempt: int) -> float:
        """
        Exponential backoff with optional retry-after parsing from error message.
        """
        message = str(exc)
        match = re.search(r"try again in ([0-9.]+)s", message, re.IGNORECASE)
        if match:
            return max(0.5, float(match.group(1)))
        return min(8.0, RAGEvaluator.BACKOFF_BASE_SEC ** attempt)

    def _parse_evaluation_json(self, model_output: str) -> Dict[str, Any]:
        """
        Validate and parse evaluator JSON output.
        """

        cleaned = (
            model_output.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Evaluator returned invalid JSON.")
            return {
                "correctness": 0,
                "faithfulness": 0,
                "helpfulness": 0,
                "context_recall": 0,
                "context_precision": 0,
                "reasoning": "Invalid JSON from evaluator.",
            }

        return {
            "correctness": int(data.get("correctness", 0)),
            "faithfulness": int(data.get("faithfulness", 0)),
            "helpfulness": int(data.get("helpfulness", 0)),
            "context_recall": int(data.get("context_recall", 0)),
            "context_precision": int(data.get("context_precision", 0)),
            "reasoning": data.get("reasoning", ""),
        }
