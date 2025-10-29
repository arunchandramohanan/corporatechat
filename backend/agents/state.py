"""
LangGraph State Schemas for Multi-Agent System

Defines the state structure that flows through the agent workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from pydantic import BaseModel


class AgentStep(BaseModel):
    """Represents a single step taken by an agent"""
    agent_name: str
    action: str  # e.g., "searching_documents", "analyzing_transaction", "creating_ticket"
    details: str
    timestamp: str
    tool_used: Optional[str] = None
    tool_output: Optional[Dict[str, Any]] = None


class AgentHandoff(BaseModel):
    """Represents a handoff between agents"""
    from_agent: str
    to_agent: str
    reason: str
    timestamp: str
    context_passed: Dict[str, Any] = {}


class AgentMessage(BaseModel):
    """Enhanced message with agent metadata"""
    text: str
    isUser: bool
    agent_name: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[Dict[str, Any]]] = None


class AgentState(TypedDict):
    """Main state object that flows through the LangGraph workflow"""
    # Input
    messages: List[Dict[str, Any]]  # Conversation history
    user_query: str  # Latest user message
    context: Dict[str, Any]  # Conversation context

    # Agent orchestration
    active_agent: Optional[str]  # Currently active agent
    consulted_agents: List[str]  # All agents consulted in this turn
    agent_steps: List[Dict[str, Any]]  # Reasoning steps taken
    agent_handoffs: List[Dict[str, Any]]  # Agent transitions

    # Tool execution
    tool_calls: List[Dict[str, Any]]  # Tools called by agents
    tool_results: List[Dict[str, Any]]  # Results from tools

    # Routing decisions
    intent: Optional[str]  # Classified user intent
    requires_collaboration: bool  # Whether multiple agents needed
    primary_agent: Optional[str]  # Main agent for this query
    secondary_agents: List[str]  # Supporting agents

    # Output
    final_response: Optional[str]  # Synthesized response
    follow_up_options: List[str]  # Suggested next actions
    quote: Optional[Dict[str, Any]]  # Card summary if applicable
    updated_context: Dict[str, Any]  # Updated conversation context

    # Metadata
    confidence_score: float  # Overall confidence in response
    escalation_required: bool  # Whether human intervention needed
    error: Optional[str]  # Error message if something failed


# Agent types
AgentType = Literal[
    "router",
    "policy",
    "account",
    "transaction",
    "analytics",
    "escalation"
]


# Intent categories
IntentCategory = Literal[
    "policy_query",
    "account_management",
    "transaction_inquiry",
    "dispute_filing",
    "analytics_request",
    "technical_support",
    "escalation",
    "general_question",
    "multi_domain"  # Requires multiple agents
]


# Tool names
ToolName = Literal[
    "rag_search",
    "get_account_info",
    "get_transactions",
    "file_dispute",
    "get_analytics",
    "create_escalation_ticket",
    "check_card_status",
    "update_spending_limit"
]
