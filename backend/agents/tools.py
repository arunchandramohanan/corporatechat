"""
Shared Tools for Multi-Agent System

Tools that agents can use to perform actions (RAG search, API calls, etc.)
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentTools:
    """Container for shared tools that agents can use"""

    def __init__(self, rag_manager=None, lambda_client=None):
        """
        Initialize agent tools.

        Args:
            rag_manager: RAGManager instance for document search
            lambda_client: Function to call Claude via Lambda
        """
        self.rag_manager = rag_manager
        self.lambda_client = lambda_client

    async def rag_search(
        self,
        query: str,
        k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search the RAG knowledge base for relevant documents.

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            Dictionary with search results and context
        """
        try:
            if not self.rag_manager:
                logger.warning("RAG manager not initialized")
                return {"success": False, "error": "RAG not available", "results": []}

            # Get search results
            results = self.rag_manager.search(query, k=k)

            # Format context
            context = self.rag_manager.get_context_for_prompt(query, k=k)

            return {
                "success": True,
                "results": results,
                "context": context,
                "num_results": len(results)
            }
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    async def call_llm(
        self,
        prompt: str,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call the LLM (Claude via Lambda) with a prompt.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt override

        Returns:
            Dictionary with LLM response and metadata
        """
        try:
            if not self.lambda_client:
                logger.warning("Lambda client not initialized")
                return {"success": False, "error": "LLM not available", "response": ""}

            # Call the Lambda function
            response = self.lambda_client(prompt, max_tokens=max_tokens)

            # Check if there was an error
            if isinstance(response, dict) and "error" in response:
                return {
                    "success": False,
                    "error": response["error"],
                    "response": ""
                }

            return {
                "success": True,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }

    def format_sources(self, rag_results: List[Dict[str, Any]]) -> str:
        """
        Format RAG search results into citation strings.

        Args:
            rag_results: List of RAG search results

        Returns:
            Formatted citation string
        """
        if not rag_results:
            return ""

        citations = []
        for result in rag_results:
            metadata = result.get("metadata", {})
            source = metadata.get("source", "Unknown")
            page = metadata.get("page", "Unknown")
            citations.append(f"[Source: {source}, Page {page}]")

        return " ".join(citations)

    def extract_key_info(self, text: str, keys: List[str]) -> Dict[str, Any]:
        """
        Extract key information from text using simple heuristics.

        Args:
            text: Text to analyze
            keys: List of keys to look for

        Returns:
            Dictionary of extracted values
        """
        # Simple keyword-based extraction
        # In a production system, this would use NER or LLM extraction
        extracted = {}
        text_lower = text.lower()

        for key in keys:
            if key.lower() in text_lower:
                extracted[key] = True
            else:
                extracted[key] = False

        return extracted


def create_agent_tools(rag_manager=None, lambda_client=None) -> AgentTools:
    """
    Factory function to create AgentTools instance.

    Args:
        rag_manager: RAGManager instance
        lambda_client: Lambda client function

    Returns:
        Configured AgentTools instance
    """
    return AgentTools(rag_manager=rag_manager, lambda_client=lambda_client)
