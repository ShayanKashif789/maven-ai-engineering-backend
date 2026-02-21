import json
import sys
import types
import unittest
from unittest.mock import patch

# ---- Lightweight stubs so tests run without external runtime deps ----
if "langchain_core.messages" not in sys.modules:
    messages_mod = types.ModuleType("langchain_core.messages")

    class _Msg:
        def __init__(self, content=""):
            self.content = content

    messages_mod.SystemMessage = _Msg
    messages_mod.HumanMessage = _Msg
    sys.modules["langchain_core.messages"] = messages_mod

if "assignments.AgenticQASystem3.core.llm_factory" not in sys.modules:
    llm_factory_mod = types.ModuleType("assignments.AgenticQASystem3.core.llm_factory")

    class _DummyLLM:
        def invoke(self, _messages):
            return types.SimpleNamespace(content='{"tone":"PROFESSIONAL","post_type":"TECHNICAL_EXPLAINER","target_format":"single_post"}')

    def _get_llm():
        return _DummyLLM()

    llm_factory_mod.get_llm = _get_llm
    sys.modules["assignments.AgenticQASystem3.core.llm_factory"] = llm_factory_mod

if "assignments.AgenticQASystem3.tools.vector_search" not in sys.modules:
    vector_mod = types.ModuleType("assignments.AgenticQASystem3.tools.vector_search")

    def _vector_search(query, k=5):
        return {"status": "success", "output": f"vector:{query}", "error": None}

    vector_mod.vector_search = _vector_search
    sys.modules["assignments.AgenticQASystem3.tools.vector_search"] = vector_mod

if "assignments.AgenticQASystem3.tools.Web_search" not in sys.modules:
    web_mod = types.ModuleType("assignments.AgenticQASystem3.tools.Web_search")

    def _web_search(query, num_results=5):
        return {"status": "success", "output": {"answer_box": f"web:{query}"}, "error": None}

    web_mod.web_search = _web_search
    sys.modules["assignments.AgenticQASystem3.tools.Web_search"] = web_mod

from assignments.MultiAgents4.agents.finalizer import finalizer_node
from assignments.MultiAgents4.agents.note_taker import note_taker_node
from assignments.MultiAgents4.agents.research_execution import research_execution_node
from assignments.MultiAgents4.agents.writing_supervisor import writing_supervisor_node
from assignments.MultiAgents4.graph.graph import (
    _should_run_research_execution,
    build_initial_state,
    run_graph,
)


class TestFinalizerNode(unittest.TestCase):
    def test_research_only_uses_research_summary(self) -> None:
        state = build_initial_state("test query")
        state["intent"] = "research_only"
        state["research_summary"] = "research answer"

        out = finalizer_node(state)
        self.assertEqual(out["final_output"], "research answer")

    def test_linkedin_prefers_edited_draft(self) -> None:
        state = build_initial_state("test query")
        state["intent"] = "linkedin_post"
        state["draft"] = "raw draft"
        state["edited_draft"] = "edited draft"

        out = finalizer_node(state)
        self.assertEqual(out["final_output"], "edited draft")


class TestWritingSupervisor(unittest.TestCase):
    def test_hot_take_maps_to_valid_tone(self) -> None:
        state = build_initial_state("write a hot take thread on ai")
        state["intent"] = "linkedin_post"

        out = writing_supervisor_node(state, enable_llm_fallback=False)
        self.assertEqual(out["tone"], "OPINIONATED")
        self.assertEqual(out["target_format"], "single_post")
        self.assertIsInstance(out["writing_plan"], dict)
        self.assertEqual(out["writing_plan"]["post_type"], "OPINION_HOT_TAKE")


class TestResearchExecution(unittest.TestCase):
    @patch("assignments.MultiAgents4.agents.research_execution.web_search")
    @patch("assignments.MultiAgents4.agents.research_execution.vector_search")
    def test_dual_source_execution_populates_both_outputs(self, mock_vector, mock_web) -> None:
        mock_vector.return_value = {
            "status": "success",
            "output": "internal facts",
            "error": None,
        }
        mock_web.return_value = {
            "status": "success",
            "output": {"answer_box": "latest update", "organic_results": []},
            "error": None,
        }

        state = build_initial_state("find internal and latest updates")
        state["research_required"] = True
        state["research_sources"] = ["vector", "web"]

        out = research_execution_node(state)

        self.assertIn("internal facts", out["vector_results"] or "")
        self.assertIn("latest update", out["web_results"] or "")
        self.assertIn("Vector Search Results", out["research_summary"] or "")
        self.assertIn("Web Search Results", out["research_summary"] or "")
        self.assertFalse(out["research_failed"])


class TestNoteTaker(unittest.TestCase):
    @patch("assignments.MultiAgents4.agents.note_taker._llm_notes")
    def test_short_summary_skips_llm(self, mock_llm_notes) -> None:
        state = build_initial_state("write linkedin post about ai agents")
        state["intent"] = "linkedin_post"
        state["tone"] = "PROFESSIONAL"
        state["target_format"] = "single_post"
        state["writing_plan"] = {"post_type": "TECHNICAL_EXPLAINER"}
        state["research_summary"] = "too short"

        out = note_taker_node(state, enable_llm_fallback=True)
        mock_llm_notes.assert_not_called()
        self.assertIsNotNone(out["notes"])
        notes_obj = json.loads(out["notes"])
        self.assertIn("key_points", notes_obj)
        self.assertGreaterEqual(len(notes_obj["key_points"]), 3)


class TestGraphFlow(unittest.TestCase):
    def test_research_condition_runs_when_one_of_two_sources_missing(self) -> None:
        state = build_initial_state("query")
        state["research_required"] = True
        state["research_sources"] = ["vector", "web"]
        state["vector_results"] = "already have vector"
        state["web_results"] = None
        self.assertTrue(_should_run_research_execution(state))

    @patch("assignments.MultiAgents4.graph.graph.draft_editor_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.draft_writer_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.note_taker_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.writing_supervisor_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.research_execution_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.research_supervisor_node", autospec=True)
    @patch("assignments.MultiAgents4.graph.graph.meta_supervisor_node", autospec=True)
    def test_graph_sets_final_output_for_research_only(
        self,
        mock_meta,
        mock_research_supervisor,
        mock_research_execution,
        mock_writing_supervisor,
        mock_note_taker,
        mock_draft_writer,
        mock_draft_editor,
    ) -> None:
        def _meta(s):
            s["intent"] = "research_only"
            s["target_team"] = "research_team"
            return s

        def _rs(s):
            s["research_required"] = True
            s["research_source"] = "web"
            s["research_sources"] = ["web"]
            return s

        def _re(s):
            s["research_summary"] = "compiled research output"
            return s

        mock_meta.side_effect = _meta
        mock_research_supervisor.side_effect = _rs
        mock_research_execution.side_effect = _re
        mock_writing_supervisor.side_effect = lambda s: s
        mock_note_taker.side_effect = lambda s: s
        mock_draft_writer.side_effect = lambda s: s
        mock_draft_editor.side_effect = lambda s: s

        state = build_initial_state("need research")
        out = run_graph(state)
        self.assertEqual(out["final_output"], "compiled research output")


if __name__ == "__main__":
    unittest.main()
