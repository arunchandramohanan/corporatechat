"""
Base Agent Class

Abstract base class for all specialized agents in the multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .state import AgentState, AgentStep

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, name: str, description: str):
        """
        Initialize the base agent.

        Args:
            name: Agent name (e.g., "PolicyAgent")
            description: What this agent does
        """
        self.name = name
        self.description = description
        self.tools = []  # Will be populated by subclasses

    @abstractmethod
    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """
        Determine if this agent can handle the current query.

        Args:
            state: Current agent state

        Returns:
            Tuple of (can_handle: bool, confidence: float)
        """
        pass

    @abstractmethod
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the agent's main logic.

        Args:
            state: Current agent state

        Returns:
            Dictionary with agent's response and updated state
        """
        pass

    def add_step(
        self,
        state: AgentState,
        action: str,
        details: str,
        tool_used: Optional[str] = None,
        tool_output: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a reasoning step to the agent's execution trace.

        Args:
            state: Current agent state
            action: Action being performed
            details: Human-readable description
            tool_used: Name of tool used (if any)
            tool_output: Output from the tool (if any)
        """
        step = {
            "agent_name": self.name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "tool_used": tool_used,
            "tool_output": tool_output
        }
        state["agent_steps"].append(step)
        logger.info(f"[{self.name}] {action}: {details}")

    def get_tools(self) -> List[str]:
        """Get list of tools this agent has access to"""
        return self.tools

    def extract_context_info(self, state: AgentState, keys: List[str]) -> Dict[str, Any]:
        """
        Extract specific information from context.

        Args:
            state: Current agent state
            keys: List of context keys to extract

        Returns:
            Dictionary with extracted values
        """
        context = state.get("context", {})
        return {key: context.get(key) for key in keys}

    def update_context(self, state: AgentState, updates: Dict[str, Any]) -> None:
        """
        Update the conversation context.

        Args:
            state: Current agent state
            updates: Dictionary of updates to apply
        """
        if "updated_context" not in state:
            state["updated_context"] = state.get("context", {}).copy()
        state["updated_context"].update(updates)

    def format_response(
        self,
        text: str,
        follow_up_options: Optional[List[str]] = None,
        quote: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format the agent's response in standard structure.

        Args:
            text: Response text
            follow_up_options: Suggested follow-up actions
            quote: Card summary or other data card

        Returns:
            Formatted response dictionary
        """
        return {
            "text": text,
            "follow_up_options": follow_up_options or [],
            "quote": quote,
            "agent_name": self.name
        }

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """
        Determine if this query should be escalated.

        Args:
            state: Current agent state

        Returns:
            Tuple of (should_escalate: bool, reason: str)
        """
        # Default implementation - can be overridden by subclasses
        return False, ""

    def get_follow_up_options(self, state: AgentState) -> List[str]:
        """
        Generate relevant follow-up options based on the interaction.

        Args:
            state: Current agent state

        Returns:
            List of follow-up suggestion strings
        """
        # Default implementation - should be overridden by subclasses
        return []

    def __repr__(self) -> str:
        return f"<{self.name}: {self.description}>"
