import asyncio
import logging
import statistics
import time
import uuid
from typing import Any, Dict, List

from langsmith import traceable

from assignments.Synthetic_RagSystem5.core.evaluator import RAGEvaluator
from assignments.Synthetic_RagSystem5.core.rag_manager import SyntheticRAGManager

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Industry-grade evaluation runner for RAG benchmarking.
    """

    MAX_EVAL_CONCURRENCY = 1
    EVAL_DELAY_SEC = 1.0

    def __init__(self, rag_manager: SyntheticRAGManager):
        self.rag = rag_manager
        self.evaluator = RAGEvaluator()

    async def run_evaluation(
        self,
        source_file: str = "",
        limit: int = 50,
    ) -> Dict[str, Any]:

        experiment_id = str(uuid.uuid4())
        start_time = time.time()

        records = await self.rag.fetch_eval_records(
            source_file=source_file,
            limit=limit,
        )

        if not records:
            return {
                "experiment_id": experiment_id,
                "total_questions": 0,
                "results": [],
            }

        semaphore = asyncio.Semaphore(self.MAX_EVAL_CONCURRENCY)

        tasks = [
            asyncio.create_task(
                self._evaluate_record(record, semaphore)
            )
            for record in records
        ]

        results = await asyncio.gather(*tasks)

        metrics = self._compute_metrics(results)

        duration = time.time() - start_time

        return {
            "experiment_id": experiment_id,
            "total_questions": len(results),
            "duration_seconds": round(duration, 2),
            "metrics": metrics,
            "results": results,
        }

    @traceable(name="rag_evaluation_record")
    async def _evaluate_record(
        self,
        record: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:

        async with semaphore:

            question = record["question"]
            reference_answer = record["reference_answer"]

            await asyncio.sleep(self.EVAL_DELAY_SEC)
            rag_result = await self.rag.aquery(question)

            rag_answer = rag_result["answer"]
            retrieved_context = rag_result["sources"]
            reference_context = record["reference_context"]
            await asyncio.sleep(self.EVAL_DELAY_SEC)
            evaluation = await self.evaluator.evaluate(
                question=question,
                reference_answer=reference_answer,
                reference_context=reference_context,
                retrieved_context=retrieved_context,
                rag_answer=rag_answer,
            )

            return {
                "question": question,
                "reference_answer": reference_answer,
                "rag_answer": rag_answer,
                "retrieved_context": retrieved_context,
                "correctness": evaluation.get("correctness", 0),
                "faithfulness": evaluation.get("faithfulness", 0),
                "context_recall": evaluation.get("context_recall", 0),
                "context_precision": evaluation.get("context_precision", 0),
                "helpfulness": evaluation.get("helpfulness", 0),
                "reasoning": evaluation.get("reasoning", ""),
            }

    def _compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        recall_scores = [r["context_recall"] for r in results]
        precision_scores = [r["context_precision"] for r in results]

        correctness_scores = [r["correctness"] for r in results]
        faithfulness_scores = [r["faithfulness"] for r in results]
        helpfulness_scores = [r["helpfulness"] for r in results]

        return {
            "avg_correctness": round(statistics.mean(correctness_scores), 2),
            "avg_faithfulness": round(statistics.mean(faithfulness_scores), 2),
            "avg_helpfulness": round(statistics.mean(helpfulness_scores), 2),
            "avg_context_recall": round(statistics.mean(recall_scores), 2),
            "avg_context_precision": round(statistics.mean(precision_scores), 2),
        }
