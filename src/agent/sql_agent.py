"""
SQL Agent with self-correction loop.
Converts natural language to SQL using Groq LLM and executes safely.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_interface import GroqLLM
from agent.prompts import PromptManager
from safety.execution_engine import SafeQueryEngine


class SQLAgent:
    """
    Natural language to SQL agent with self-correction.
    
    Features:
    - Converts questions to SQL using Groq LLM
    - Executes queries safely with validation
    - Auto-corrects failed queries (up to max_retries)
    - Interprets results in business-friendly language
    - Tracks conversation history
    """
    
    def __init__(
        self, 
        db_path: str,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        max_retries: int = 2,
        temperature: float = 0.1
    ):
        """
        Initialize SQL agent.
        
        Args:
            db_path: Path to SQLite database
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Groq model to use
            max_retries: Max correction attempts for failed queries
            temperature: LLM temperature (lower = more deterministic)
        """
        self.llm = GroqLLM(api_key=api_key, model=model)
        self.engine = SafeQueryEngine(db_path)
        self.prompts = PromptManager()
        self.max_retries = max_retries
        self.temperature = temperature
        
        self.conversation_history: List[Dict[str, Any]] = []
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Main interface: ask a question in natural language.
        
        Args:
            question: Natural language question about the data
            
        Returns:
            Dict with:
                - success: bool
                - question: original question
                - sql_query: generated SQL
                - results: query results (if successful)
                - interpretation: business-friendly summary
                - error: error message (if failed)
                - retries: number of correction attempts
                - execution_time_ms: query execution time
                - timestamp: when query was run
        """
        start_time = datetime.now()
        
        response = {
            "success": False,
            "question": question,
            "sql_query": None,
            "results": None,
            "interpretation": None,
            "error": None,
            "retries": 0,
            "execution_time_ms": 0,
            "timestamp": start_time.isoformat()
        }
        
        try:
            # Step 1: Generate SQL from question
            sql_query = self._generate_sql(question)
            response["sql_query"] = sql_query
            
            # Step 2: Execute with self-correction loop
            execution_result = self._execute_with_retry(question, sql_query)
            
            response["retries"] = execution_result["retries"]
            response["sql_query"] = execution_result["final_query"]
            
            if execution_result["success"]:
                response["success"] = True
                response["results"] = execution_result["data"]
                response["execution_time_ms"] = execution_result["execution_time_ms"]
                
                # Step 3: Interpret results
                interpretation = self._interpret_results(
                    question, 
                    execution_result["final_query"],
                    execution_result["data"]
                )
                response["interpretation"] = interpretation
            else:
                response["error"] = execution_result["error"]
            
        except Exception as e:
            response["error"] = f"Agent error: {str(e)}"
        
        # Track conversation
        self.conversation_history.append(response)
        
        return response
    
    def _generate_sql(self, question: str, schema_context: str = "") -> str:
        """Generate SQL query from natural language question."""
        prompt = self.prompts.get_sql_generation_prompt(question, schema_context)
        
        sql_query = self.llm.generate(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=1024
        )
        
        # Clean up response (remove markdown, extra whitespace)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        return sql_query
    
    def _execute_with_retry(self, question: str, initial_query: str) -> Dict[str, Any]:
        """
        Execute query with self-correction loop.
        
        Tries to execute query, and if it fails, asks LLM to correct it.
        Repeats up to max_retries times.
        """
        current_query = initial_query
        retries = 0
        
        for attempt in range(self.max_retries + 1):
            # Try to execute
            result = self.engine.execute_query(current_query)
            
            if result["success"]:
                return {
                    "success": True,
                    "final_query": current_query,
                    "data": result["data"],
                    "execution_time_ms": result["execution_time_ms"],
                    "retries": retries
                }
            
            # If failed and we have retries left, try to correct
            if attempt < self.max_retries:
                retries += 1
                error_message = result["error"]
                
                # Ask LLM to correct the query
                correction_prompt = self.prompts.get_correction_prompt(
                    question, current_query, error_message
                )
                
                corrected_query = self.llm.generate(
                    prompt=correction_prompt,
                    temperature=self.temperature,
                    max_tokens=1024
                )
                
                # Clean up corrected query
                corrected_query = corrected_query.strip()
                if corrected_query.startswith("```sql"):
                    corrected_query = corrected_query.replace("```sql", "").replace("```", "").strip()
                elif corrected_query.startswith("```"):
                    corrected_query = corrected_query.replace("```", "").strip()
                
                current_query = corrected_query
            else:
                # Out of retries
                return {
                    "success": False,
                    "final_query": current_query,
                    "error": result["error"],
                    "retries": retries
                }
        
        # Should not reach here
        return {
            "success": False,
            "final_query": current_query,
            "error": "Unknown error",
            "retries": retries
        }
    
    def _interpret_results(self, question: str, query: str, results: List[Dict]) -> str:
        """Generate business-friendly interpretation of results."""
        # Format results for LLM
        if not results:
            results_str = "No results found."
        elif len(results) <= 5:
            results_str = json.dumps(results, indent=2)
        else:
            # Show first 3 and last 2 for large result sets
            sample = results[:3] + results[-2:]
            results_str = json.dumps(sample, indent=2)
            results_str += f"\n... ({len(results)} total rows)"
        
        prompt = self.prompts.get_interpretation_prompt(question, query, results_str)
        
        interpretation = self.llm.generate(
            prompt=prompt,
            temperature=0.3,  # Slightly higher for more natural language
            max_tokens=512
        )
        
        return interpretation.strip()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information."""
        return self.engine.get_schema()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get all queries from current session."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_queries = len(self.conversation_history)
        successful = sum(1 for q in self.conversation_history if q["success"])
        failed = total_queries - successful
        
        total_retries = sum(q["retries"] for q in self.conversation_history)
        avg_retries = total_retries / total_queries if total_queries > 0 else 0
        
        avg_time = sum(q["execution_time_ms"] for q in self.conversation_history if q["success"]) / successful if successful > 0 else 0
        
        return {
            "total_queries": total_queries,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total_queries*100):.1f}%" if total_queries > 0 else "0%",
            "total_retries": total_retries,
            "avg_retries_per_query": round(avg_retries, 2),
            "avg_execution_time_ms": round(avg_time, 2)
        }
