"""
Analysis Agent - Specialized in requirements analysis and data extraction
"""

import sys
import os
import json
import re
import logging
from typing import Dict, Any, List
from datetime import datetime
from strands import Agent
from strands.models import OpenAIModel

# Add parent directory to path for tools import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import specialized file analysis agents
from .pdf_analysis_agent import PDFAnalysisAgent
from .docx_analysis_agent import DocxAnalysisAgent
from .xlsx_analysis_agent import XlsxAnalysisAgent
from .csv_analysis_agent import CsvAnalysisAgent
from .txt_analysis_agent import TxtAnalysisAgent

# Import file source handlers
from tools.workspace_file_detector import WorkspaceFileDetector

ANALYSIS_AGENT_PROMPT = """
You are a specialized Requirements Analysis Agent for technical architecture proposals.

Your role is to:
1. Analyze client input (text, requirements, business needs)
2. Consult file contents when provided (PDFs, documents, spreadsheets)
3. Extract key information: project name, client name, technologies, scope, timeline
4. Consult Notion cache for validated scopes and rules when supplied
5. Identify data gaps that need clarification
6. Structure the analysis in a clear JSON format

IMPORTANT: You have access to Notion via tools, but the orchestrator will
usually pass cached page content.  Use the cache first and avoid new API
queries unless you truly need to.
"""

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Analysis Agent using Strands with optional Notion MCP access and file analysis capabilities
    
    Responsibilities:
    - Process multiple input formats (text, transcripts, emails)
    - Extract key information (project, client, technologies, scope)
    - Analyze uploaded files (PDF, DOCX, XLSX, CSV, TXT) using specialized agents
    - Fetch validated scopes from Notion when necessary
    - Identify data gaps
    """
    
    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Build tools list - if MCPClient provided, pass it directly to Agent
        tools = [notion_mcp_client] if notion_mcp_client else []
        
        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 2,
                    "timeout": 90,
                },
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.3,
                    "max_tokens": 1200
                }
            ),
            system_prompt=ANALYSIS_AGENT_PROMPT,
            tools=tools,
            callback_handler=None,
        )
        
        # Initialize specialized file analysis agents
        self.file_agents = {
            '.pdf': PDFAnalysisAgent(),
            '.docx': DocxAnalysisAgent(),
            '.xlsx': XlsxAnalysisAgent(),
            '.xls': XlsxAnalysisAgent(),  # Also handle .xls with xlsx agent
            '.csv': CsvAnalysisAgent(),
            '.txt': TxtAnalysisAgent()
        }

        # Initialize file source handlers
        self.workspace_detector = WorkspaceFileDetector()

    def _analyze_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Internal method to analyze multiple files using specialized agents
        
        Args:
            file_paths: List of local file paths to analyze
            
        Returns:
            Dict with individual analyses, consolidated text, and summary
        """
        logger.info(f"[AnalysisAgent] Analyzing {len(file_paths)} files with specialized agents")
        
        individual_analyses = {}
        all_text = []
        all_tables = []
        errors = []
        
        for file_path in file_paths:
            try:
                # Local file
                actual_path = file_path
                
                # Get file extension and find appropriate agent
                from pathlib import Path
                path = Path(actual_path)
                suffix = path.suffix.lower()
                
                if suffix not in self.file_agents:
                    error_msg = f"Unsupported file format: {suffix}"
                    file_name = Path(file_path).name
                    individual_analyses[file_name] = {
                        'extracted_text': error_msg,
                        'extracted_data': {},
                        'file_info': {
                            'path': file_path,
                            'type': suffix,
                            'error': error_msg,
                            'source': 's3' if is_s3 else 'local'
                        }
                    }
                    errors.append(f"{file_name}: {error_msg}")
                    continue
                
                # Analyze with specialized agent
                agent = self.file_agents[suffix]
                result = agent.analyze(path)
                
                # Add source information
                file_name = Path(file_path).name
                result['file_info'] = {
                    'path': file_path,
                    'type': suffix,
                    'size': path.stat().st_size,
                    'source': 'local'
                }
                
                individual_analyses[file_name] = result
                
                # Consolidate content
                if "extracted_text" in result:
                    all_text.append(f"--- {file_name} ---\n{result['extracted_text']}")
                    
                if "extracted_data" in result and "tables" in result["extracted_data"]:
                    all_tables.extend(result["extracted_data"]["tables"])
                    
            except Exception as e:
                logger.error(f"[AnalysisAgent] Error analyzing {file_path}: {e}")
                file_name = Path(file_path).name
                individual_analyses[file_name] = {
                    'extracted_text': f"Analysis failed: {e}",
                    'extracted_data': {},
                    'file_info': {
                        'path': file_path,
                        'error': str(e),
                        'source': 'local'
                    }
                }
                errors.append(f"{file_name}: {e}")
        
        # Create consolidated text
        consolidated_text = "\n\n".join(all_text) if all_text else ""
        
        # Generate summary
        summary = self._generate_file_analysis_summary(individual_analyses, consolidated_text)
        
        return {
            "individual_analyses": individual_analyses,
            "consolidated_text": consolidated_text,
            "consolidated_tables": all_tables,
            "summary": summary,
            "errors": errors,
            "total_files": len(file_paths),
            "successful_analyses": len(file_paths) - len(errors),
            "batch_processed_at": datetime.now().isoformat()
        }

    def _generate_file_analysis_summary(self, analyses: Dict[str, Any], consolidated_text: str) -> str:
        """Generate a summary of all analyzed files."""
        total_files = len(analyses)
        successful = sum(1 for a in analyses.values() if "error" not in a and "file_info" in a and "error" not in a["file_info"])
        failed = total_files - successful

        summary_parts = [
            f"Análise de {total_files} arquivo(s):",
            f"✅ Sucesso: {successful}",
            f"❌ Falha: {failed}"
        ]

        if consolidated_text:
            word_count = len(consolidated_text.split())
            summary_parts.append(f"📝 Texto extraído: ~{word_count} palavras")

        # Count tables
        total_tables = 0
        for analysis in analyses.values():
            if "extracted_data" in analysis and "tables" in analysis["extracted_data"]:
                total_tables += len(analysis["extracted_data"]["tables"])

        if total_tables > 0:
            summary_parts.append(f"📊 Tabelas encontradas: {total_tables}")

        return " | ".join(summary_parts)

    def analyze(self, input_text: str, input_type: str = "text", notion_cache: str = "", file_paths: List[str] = None, auto_detect_files: bool = False) -> Dict[str, Any]:
        """
        Analyze input and extract requirements, including file contents when provided
        
        Args:
            input_text: Client input to analyze
            input_type: Type of input (text, transcript, email, etc.)
            notion_cache: Pre-fetched Notion content that can be used as reference
            file_paths: List of file paths or S3 URLs to analyze (PDF, DOCX, XLSX, CSV, TXT)
            auto_detect_files: If True, automatically detect relevant files in current workspace
        
        Returns:
            Analysis result with extracted info, Notion scopes, data gaps, and file analyses
        """
        logger.info("[AnalysisAgent] Iniciando análise...")
        
        # Edge case: input_text must be non-empty string
        if not isinstance(input_text, str) or not input_text.strip():
            logger.warning("[AnalysisAgent] input_text vazio ou inválido.")
            return {"error": "input_text must be a non-empty string", "status": "analysis_failed"}
        
        # Unicode normalization
        input_text = input_text.encode("utf-8", errors="replace").decode("utf-8")
        logger.info("[AnalysisAgent] Input normalizado para UTF-8.")
        
        # Handle auto-detection of files in workspace
        if auto_detect_files and not file_paths:
            logger.info("[AnalysisAgent] Auto-detecting relevant files in workspace...")
            try:
                detected_files = self.workspace_detector.detect_relevant_files()
                file_paths = [f['path'] for f in detected_files[:10]]  # Limit to top 10 most relevant
                logger.info(f"[AnalysisAgent] Auto-detected {len(file_paths)} relevant files")
            except Exception as e:
                logger.warning(f"[AnalysisAgent] Auto-detection failed: {e}")
                file_paths = []

        # Analyze files if provided
        file_context = ""
        file_analyses = {}
        if file_paths and len(file_paths) > 0:
            logger.info(f"[AnalysisAgent] Analisando {len(file_paths)} arquivo(s)...")
            try:
                batch_result = self._analyze_files(file_paths)
                file_analyses = batch_result.get("individual_analyses", {})
                file_context = batch_result.get("consolidated_text", "")
                
                # Add file summary to context
                if batch_result.get("summary"):
                    file_context = f"RESUMO DOS ARQUIVOS:\n{batch_result['summary']}\n\nCONTEÚDO EXTRAÍDO:\n{file_context}"
                
                logger.info(f"[AnalysisAgent] Análise de arquivos concluída: {batch_result.get('successful_analyses', 0)}/{len(file_paths)} sucesso")
            except Exception as e:
                logger.warning(f"[AnalysisAgent] Falha na análise de arquivos: {e}")
                file_context = f"AVISO: Não foi possível analisar os arquivos fornecidos. Erro: {e}\n\n"
        
        # attach cache to prompt if available
        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        
        # Build comprehensive prompt with file context
        prompt = f"""
{cache_section}
{file_context}
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: {input_type}
INPUT:
{input_text}

INSTRUCTIONS:
1. Consult only the cached Notion pages above for rules, examples and templates.
2. Use the file contents provided above as primary reference material.
3. Do not call external tools during this analysis.
4. Extract all key information from the input AND file contents.
5. Use objective language and keep output compact.
6. Identify only CRITICAL data gaps (information absolutely needed to proceed).

Provide your analysis in JSON format:
{{
  "clientInfo": {{
    "companyName": "string or null",
    "projectName": "string or null",
    "contactEmail": "string or null",
    "contactPerson": "string or null"
  }},
  "businessRequirements": ["requirement1", "requirement2"],
  "technicalRequirements": ["requirement1", "requirement2"],
  "scope": {{
    "included": ["item1", "item2"],
    "excluded": ["item1", "item2"]
  }},
  "technologies": ["tech1", "tech2"],
  "constraints": ["constraint1", "constraint2"],
  "timeline": "string or null",
  "budget": "string or null",
  "notionScopes": [
    {{
      "id": "scope_id_from_notion",
      "title": "Scope title",
      "description": "Scope description",
      "hours": 0,
      "technologies": ["tech1"]
    }}
  ],
  "confidence": 0.0-1.0,
  "dataGaps": [
    {{
      "field": "field_name",
      "description": "why this is needed",
      "required": true,
      "suggestedQuestions": ["question1", "question2"]
    }}
  ]
}}

Note: minimize Notion API calls to conserve rate limits.
"""
        try:
            result = self.agent(prompt)
            result_text = str(result)
            logger.info("[AnalysisAgent] Resultado recebido.")
            # Try to extract JSON from result
            analysis_data = None
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
            except Exception as e:
                logger.warning("[AnalysisAgent] Could not parse JSON from result: %s", e)
            # Return serializable data
            if analysis_data and isinstance(analysis_data, dict):
                logger.info("[AnalysisAgent] JSON extraído com sucesso.")
                return {
                    "analysis": analysis_data,
                    "file_analyses": file_analyses,
                    "input_text": input_text,
                    "input_type": input_type,
                    "file_paths": file_paths or [],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.info("[AnalysisAgent] JSON não extraído, retornando texto bruto.")
                return {
                    "analysis": result_text,
                    "file_analyses": file_analyses,
                    "input_text": input_text,
                    "input_type": input_type,
                    "file_paths": file_paths or [],
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.exception("[AnalysisAgent] ERROR — %s: %s", type(e).__name__, e)
            # Log the full exception chain for diagnosing connection errors
            cause = e.__cause__ or e.__context__
            while cause:
                logger.error("[AnalysisAgent]   caused by %s: %s", type(cause).__name__, cause)
                cause = getattr(cause, '__cause__', None) or getattr(cause, '__context__', None)
            return {"error": str(e), "status": "analysis_failed"}
