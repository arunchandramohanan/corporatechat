"""
Policy Agent

Specialized agent for handling policy queries, card benefits, fees, and program information.
Uses RAG to retrieve information from policy documents.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from .state import AgentState
from .tools import AgentTools

logger = logging.getLogger(__name__)


class PolicyAgent(BaseAgent):
    """Agent specialized in corporate card policies and programs"""

    def __init__(self, tools: AgentTools):
        super().__init__(
            name="PolicyAgent",
            description="Expert in corporate card policies, benefits, fees, and program information"
        )
        self.tools_instance = tools
        self.tools = ["rag_search", "call_llm"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """
        Determine if this agent can handle the query.

        Args:
            state: Current agent state

        Returns:
            (can_handle, confidence)
        """
        query = state.get("user_query", "").lower()
        intent = state.get("intent", "")

        # Policy-related keywords
        policy_keywords = [
            "policy", "benefit", "eligibility", "credit limit", "fee",
            "rewards", "program", "insurance", "protection", "coverage",
            "annual fee", "interest rate", "apr", "cash advance",
            "foreign transaction", "travel", "purchase protection",
            "extended warranty", "what is", "explain", "tell me about",
            "how does", "what are the"
        ]

        # Check for policy intent
        if intent == "policy_query":
            return True, 0.95

        # Check for policy keywords
        keyword_matches = sum(1 for keyword in policy_keywords if keyword in query)

        if keyword_matches >= 2:
            return True, 0.90
        elif keyword_matches == 1:
            return True, 0.70

        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute policy query handling.

        Args:
            state: Current agent state

        Returns:
            Agent response with policy information
        """
        try:
            query = state.get("user_query", "")
            context = state.get("context", {})

            # Step 1: Search RAG for relevant policy documents
            self.add_step(
                state,
                action="searching_policy_documents",
                details=f"Searching corporate card policy documents for: {query}",
                tool_used="rag_search"
            )

            rag_result = await self.tools_instance.rag_search(query, k=3)

            # Step 2: Check if RAG returned results
            rag_context = ""
            rag_results = []
            has_rag_info = False

            if rag_result.get("success") and rag_result.get("results"):
                rag_context = rag_result.get("context", "")
                rag_results = rag_result.get("results", [])
                has_rag_info = len(rag_results) > 0

                self.add_step(
                    state,
                    action="documents_retrieved",
                    details=f"Found {len(rag_results)} relevant document sections",
                    tool_output={"num_results": len(rag_results)}
                )
            else:
                self.add_step(
                    state,
                    action="no_documents_found",
                    details="No policy documents found in RAG, will answer from general knowledge",
                    tool_output=rag_result
                )

            # Step 3: Build prompt for LLM (works with or without RAG)
            prompt = self._build_policy_prompt(query, rag_context, context, has_rag_info)

            self.add_step(
                state,
                action="generating_response",
                details="Generating policy answer using retrieved documents",
                tool_used="call_llm"
            )

            # Step 4: Call LLM for synthesis
            llm_result = await self.tools_instance.call_llm(prompt, max_tokens=1024)

            if not llm_result.get("success"):
                return self._handle_llm_error(state, llm_result.get("error", "Unknown error"))

            response_text = llm_result.get("response", "")

            # Step 5: Update context
            self.update_context(state, {
                "support_category": "policy",
                "consulted_documents": len(rag_results),
                "last_policy_query": query
            })

            # Step 6: Generate follow-up options
            follow_ups = self.get_follow_up_options(state)

            self.add_step(
                state,
                action="response_complete",
                details=f"Successfully answered policy question" + (f" with {len(rag_results)} source citations" if len(rag_results) > 0 else " from general knowledge")
            )

            return self.format_response(
                text=response_text,
                follow_up_options=follow_ups,
                quote=None
            )

        except Exception as e:
            logger.error(f"Error in PolicyAgent execution: {e}")
            state["error"] = str(e)
            return self.format_response(
                text="I apologize, but I encountered an error while searching our policy documents. Please try rephrasing your question or contact support.",
                follow_up_options=["View policy documents", "Contact support", "Ask another question"]
            )

    def _build_policy_prompt(self, query: str, rag_context: str, conversation_context: Dict[str, Any], has_rag_info: bool) -> str:
        """Build the prompt for policy queries"""

        if has_rag_info and rag_context.strip():
            # Case 1: We have relevant policy documents from RAG
            return f"""You are a BMO Corporate Card policy expert assistant. Answer the cardholder's question using the policy information below.

POLICY INFORMATION:
{rag_context}

Cardholder's Question: {query}

FORMATTING REQUIREMENTS - VERY IMPORTANT:
- Format your response using simple HTML only (NO markdown)
- Use basic HTML tags: <h3>, <h4>, <p>, <ul>, <li>, <table>, <strong>
- Keep styling minimal - use simple tables with borders
- Gray header for tables: background-color: #f0f0f0
- Standard padding: 8px
- NEVER use markdown syntax (**, ##, -, *)
- NO colored boxes or excessive styling
- USE COMPACT VERTICAL SPACING: Minimize blank lines between elements - no double line breaks
- Keep response dense with minimal whitespace between paragraphs, lists, and sections

Content Instructions:
1. Answer the question directly and professionally as BMO's representative
2. If the policy information above contains the answer, use it and cite sources: (<a href="document_link" style="color: #0066cc;">Source: Document Name, Page X</a>)
3. If the policy information above doesn't contain the answer, provide a helpful general answer based on common corporate card practices
4. Include specific policy details (fees, limits, percentages, etc.) when available
5. Be concise but comprehensive
6. Use HTML bullet points (<ul><li>) for multiple related points
7. Speak definitively as BMO's representative - avoid "typically" or "usually"

ABSOLUTELY CRITICAL - NEVER EVER SAY THESE PHRASES:
- "The retrieved policy documents do not specify"
- "The policy documents do not contain"
- "The documents do not address"
- "Retrieved documents"
- "Policy documents"
- "Available documents"
- "Documentation does not include"
- "No information available"
- "Not covered in documents"
- "Documents don't have"
- Or ANY variation that mentions checking, retrieving, or consulting documents

NEVER mention or reference:
- That you searched or checked documents
- That documents are missing information
- That information is not in documents
- AWS, cloud services, S3, Lambda, or technical systems

INSTEAD: Answer naturally as a knowledgeable BMO representative. If you need to defer to official sources, simply say:
"For specific details on this, please check your cardholder agreement or contact your account administrator."

DO NOT explain why you're deferring - just provide helpful general information and suggest they contact support for specifics.

Provide your HTML-formatted answer now:"""
        else:
            # Case 2: No relevant documents in RAG - answer from general knowledge
            return f"""You are a BMO Corporate Card policy expert assistant. Answer the cardholder's question about corporate card policies.

NOTE: Specific policy documents are not available for this query, so provide a helpful general answer based on common corporate card practices.

Cardholder's Question: {query}

FORMATTING REQUIREMENTS - VERY IMPORTANT:
- Format your response using simple HTML only (NO markdown)
- Use basic HTML tags: <h3>, <h4>, <p>, <ul>, <li>, <table>, <strong>
- Keep styling minimal - use simple tables with borders
- Gray header for tables: background-color: #f0f0f0
- Standard padding: 8px
- NEVER use markdown syntax (**, ##, -, *)
- NO colored boxes or excessive styling
- USE COMPACT VERTICAL SPACING: Minimize blank lines between elements - no double line breaks
- Keep response dense with minimal whitespace between paragraphs, lists, and sections

Content Instructions:
1. Provide a helpful, professional answer about corporate card policies
2. Answer based on general banking and corporate card knowledge
3. Be clear that for specific BMO policy details, they should consult their cardholder agreement or contact support
4. Do NOT make up specific fees, rates, or limits - speak in general terms
5. Be concise but informative
6. Use HTML bullet points (<ul><li>) for clarity
7. Speak professionally as BMO's representative
8. Suggest they can contact support for specific policy details if needed
9. Do NOT mention that documents are unavailable or missing - just answer naturally

Example simple HTML:
<h3>Topic</h3>
<p>Content here...</p>
<ul>
  <li>Point 1</li>
  <li>Point 2</li>
</ul>
<p>For specific BMO policies, contact support.</p>

Provide your HTML-formatted answer now:"""

    def _handle_no_documents(self, state: AgentState, query: str) -> Dict[str, Any]:
        """Handle case when no documents are found"""
        return self.format_response(
            text="I couldn't find specific policy information about that in our documentation. Let me connect you with a support specialist who can help with your specific question.",
            follow_up_options=[
                "Contact support",
                "View all policy documents",
                "Ask a different question"
            ]
        )

    def _handle_llm_error(self, state: AgentState, error: str) -> Dict[str, Any]:
        """Handle LLM errors"""
        logger.error(f"LLM error in PolicyAgent: {error}")
        return self.format_response(
            text="I'm having trouble processing your question right now. Please try again in a moment, or I can connect you with a support specialist.",
            follow_up_options=["Try again", "Contact support"]
        )

    def get_follow_up_options(self, state: AgentState) -> List[str]:
        """Generate relevant follow-up options"""
        query = state.get("user_query", "").lower()

        # Customize follow-ups based on query topic
        if any(word in query for word in ["fee", "charge", "cost"]):
            return [
                "What other fees apply?",
                "How can I avoid fees?",
                "View fee schedule"
            ]
        elif any(word in query for word in ["reward", "point", "redeem"]):
            return [
                "How do I redeem rewards?",
                "Check my rewards balance",
                "What's my earning rate?"
            ]
        elif any(word in query for word in ["travel", "international", "foreign"]):
            return [
                "Travel insurance details",
                "Foreign transaction fees",
                "Travel notification"
            ]
        elif any(word in query for word in ["benefit", "insurance", "protection"]):
            return [
                "How to file a claim",
                "Coverage limits",
                "View all benefits"
            ]
        else:
            return [
                "View all card benefits",
                "Fee schedule",
                "Ask another policy question"
            ]

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """Determine if query should be escalated"""
        query = state.get("user_query", "").lower()

        # Escalate complex policy disputes or complaints
        escalation_triggers = [
            "complaint",
            "dispute policy",
            "disagree with",
            "unfair",
            "manager",
            "supervisor"
        ]

        for trigger in escalation_triggers:
            if trigger in query:
                return True, f"Policy complaint or dispute detected: {trigger}"

        return False, ""
