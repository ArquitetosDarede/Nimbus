"""
Agents module — Specialized agents for proposal generation (v2 architecture).

This module contains:
- AnalysisAgent: Analyzes client input and extracts requirements
- ArchitectureAgent: Produces authoritative architecture contract + security evaluation
- NotionRelevanceMapper: Maps template sections to relevant Notion pages
- WriterAgent: Unified section writer (replaces business/technical split)
- GenerationAgent: Orchestrates per-section generation using WriterAgent
- CoherenceAgent: Post-generation contradiction detection
- ScoreEvaluatorAgent: Evaluates proposal against SCORE - Consulting criteria
- ConversionAgent: Converts proposals to different formats
- OrchestratorAgent: Coordinates the full workflow
- InteractionAgent: Natural-language answer extraction
"""

from .analysis_agent import AnalysisAgent
from .architecture_agent import ArchitectureAgent
from .coherence_agent import CoherenceAgent
from .conversion_agent import ConversionAgent
from .generation_agent_v2 import GenerationAgent
from .interaction_agent import InteractionAgent
from .notion_relevance_mapper import NotionRelevanceMapper
from .orchestrator_v2 import OrchestratorAgent
from .score_evaluator_agent import ScoreEvaluatorAgent
from .writer_agent import WriterAgent

__all__ = [
    "AnalysisAgent",
    "ArchitectureAgent",
    "CoherenceAgent",
    "ConversionAgent",
    "GenerationAgent",
    "InteractionAgent",
    "NotionRelevanceMapper",
    "OrchestratorAgent",
    "ScoreEvaluatorAgent",
    "WriterAgent",
]
