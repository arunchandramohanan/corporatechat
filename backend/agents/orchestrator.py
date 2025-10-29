"""
Agent Orchestrator

LangGraph-based orchestrator that routes queries to appropriate agents
and coordinates multi-agent collaboration.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END
from .state import AgentState, IntentCategory
from .base_agent import BaseAgent
from .policy_agent import PolicyAgent
from .account_agent import AccountAgent
from .transaction_agent import TransactionAgent
from .analytics_agent import AnalyticsAgent
from .escalation_agent import EscalationAgent
from .tools import AgentTools

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multi-agent workflows using LangGraph"""

    def __init__(
        self,
        rag_manager=None,
        lambda_client=None,
        account_service=None,
        transaction_service=None,
        analytics_service=None
    ):
        """Initialize orchestrator with all required services"""
        # Create shared tools
        self.tools = AgentTools(rag_manager=rag_manager, lambda_client=lambda_client)

        # Initialize all agents
        self.agents: Dict[str, BaseAgent] = {
            "policy": PolicyAgent(self.tools),
            "account": AccountAgent(self.tools, account_service),
            "transaction": TransactionAgent(self.tools, transaction_service),
            "analytics": AnalyticsAgent(self.tools, analytics_service),
            "escalation": EscalationAgent(self.tools)
        }

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine for agent orchestration"""
        workflow = StateGraph(AgentState)

        # Add nodes for each stage
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_primary_agent", self._execute_primary_agent)
        workflow.add_node("check_collaboration", self._check_collaboration)
        workflow.add_node("execute_secondary_agents", self._execute_secondary_agents)
        workflow.add_node("synthesize_response", self._synthesize_response)
        workflow.add_node("check_escalation", self._check_escalation)

        # Define the workflow edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_primary_agent")
        workflow.add_edge("execute_primary_agent", "check_collaboration")

        # Conditional edges based on collaboration need
        workflow.add_conditional_edges(
            "check_collaboration",
            self._should_collaborate,
            {
                True: "execute_secondary_agents",
                False: "check_escalation"
            }
        )

        workflow.add_edge("execute_secondary_agents", "synthesize_response")
        workflow.add_edge("synthesize_response", "check_escalation")

        # Conditional edges for escalation
        workflow.add_conditional_edges(
            "check_escalation",
            self._needs_escalation,
            {
                True: "route_to_agent",  # Re-route to escalation agent
                False: END
            }
        )

        return workflow.compile()

    async def process_message(self, messages: List[Dict], context: Dict) -> Dict[str, Any]:
        """
        Process a user message through the multi-agent workflow.

        Args:
            messages: Conversation history
            context: Current conversation context

        Returns:
            Response dictionary with agent outputs
        """
        try:
            # Get the latest user message
            user_query = ""
            for msg in reversed(messages):
                if msg.get("isUser"):
                    user_query = msg.get("text", "")
                    break

            # Initialize state
            initial_state: AgentState = {
                "messages": messages,
                "user_query": user_query,
                "context": context,
                "active_agent": None,
                "consulted_agents": [],
                "agent_steps": [],
                "agent_handoffs": [],
                "tool_calls": [],
                "tool_results": [],
                "intent": None,
                "requires_collaboration": False,
                "primary_agent": None,
                "secondary_agents": [],
                "final_response": None,
                "follow_up_options": [],
                "quote": None,
                "updated_context": context.copy(),
                "confidence_score": 0.0,
                "escalation_required": False,
                "error": None
            }

            # Run the workflow
            logger.info(f"Processing query: {user_query[:50]}...")
            final_state = await self.workflow.ainvoke(initial_state)

            # Format the response
            response = {
                "text": final_state.get("final_response", "I apologize, but I'm having trouble processing your request."),
                "isUser": False,
                "active_agent": final_state.get("active_agent"),
                "consulted_agents": final_state.get("consulted_agents", []),
                "agent_steps": final_state.get("agent_steps", []),
                "agent_handoffs": final_state.get("agent_handoffs", []),
                "follow_up_options": final_state.get("follow_up_options", []),
                "quote": final_state.get("quote"),
                "context": final_state.get("updated_context", context),
                "confidence_score": final_state.get("confidence_score", 0.0)
            }

            logger.info(f"Response generated by {response['active_agent']} with {len(response['consulted_agents'])} agents consulted")

            return response

        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)
            return {
                "text": "I apologize, but I encountered an error processing your request. Please try again or contact support.",
                "isUser": False,
                "active_agent": "error_handler",
                "consulted_agents": [],
                "agent_steps": [],
                "agent_handoffs": [],
                "follow_up_options": ["Try again", "Contact support"],
                "quote": None,
                "context": context,
                "confidence_score": 0.0
            }

    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify the user's intent"""
        query = state["user_query"].lower()

        # Simple rule-based intent classification
        # In production, this could use an LLM or ML classifier
        if any(word in query for word in ["policy", "benefit", "fee", "eligibility", "what is", "explain"]):
            state["intent"] = "policy_query"
        elif any(word in query for word in ["balance", "limit", "account", "credit", "authorized user"]):
            state["intent"] = "account_management"
        elif any(word in query for word in ["transaction", "charge", "statement", "purchase"]):
            state["intent"] = "transaction_inquiry"
        elif any(word in query for word in ["dispute", "fraud", "unauthorized"]):
            state["intent"] = "dispute_filing"
        elif any(word in query for word in ["analytics", "spending", "trend", "report", "budget"]):
            state["intent"] = "analytics_request"
        elif any(word in query for word in ["escalate", "manager", "complaint", "speak to"]):
            state["intent"] = "escalation"
        else:
            state["intent"] = "general_question"

        # Check if multi-domain (requires multiple agents)
        domain_keywords = {
            "policy": ["policy", "benefit", "fee"],
            "account": ["balance", "limit", "account"],
            "transaction": ["transaction", "charge"],
            "analytics": ["analytics", "spending", "report"]
        }

        domains_mentioned = sum(
            1 for keywords in domain_keywords.values()
            if any(kw in query for kw in keywords)
        )

        if domains_mentioned >= 2:
            state["intent"] = "multi_domain"
            state["requires_collaboration"] = True

        logger.info(f"Classified intent as: {state['intent']}")
        return state

    def _route_to_agent(self, state: AgentState) -> AgentState:
        """Route to the most appropriate primary agent"""
        # If escalation is required from a previous step, route to escalation agent
        if state.get("escalation_required"):
            state["primary_agent"] = "escalation"
            state["active_agent"] = "escalation"
            logger.info("Routing to EscalationAgent (escalation required)")
            return state

        # Ask each agent if they can handle this query
        best_agent = None
        best_confidence = 0.0

        for agent_name, agent in self.agents.items():
            can_handle, confidence = agent.can_handle(state)

            if can_handle and confidence > best_confidence:
                best_agent = agent_name
                best_confidence = confidence

        # Default to policy agent if no clear winner
        if not best_agent:
            best_agent = "policy"
            best_confidence = 0.5

        state["primary_agent"] = best_agent
        state["active_agent"] = best_agent
        state["confidence_score"] = best_confidence

        logger.info(f"Routed to {best_agent} agent (confidence: {best_confidence:.2f})")
        return state

    async def _execute_primary_agent(self, state: AgentState) -> AgentState:
        """Execute the primary agent"""
        agent_name = state["primary_agent"]
        agent = self.agents[agent_name]

        logger.info(f"Executing {agent_name} agent...")

        # Record agent consultation
        if agent_name not in state["consulted_agents"]:
            state["consulted_agents"].append(agent_name)

        # Execute the agent
        result = await agent.execute(state)

        # Store the primary response
        state["primary_response"] = result
        state["final_response"] = result.get("text", "")
        state["follow_up_options"] = result.get("follow_up_options", [])
        state["quote"] = result.get("quote")

        # Check if agent recommends escalation
        should_escalate, reason = agent.should_escalate(state)
        if should_escalate:
            state["escalation_required"] = True
            logger.info(f"Agent {agent_name} recommends escalation: {reason}")

        return state

    def _check_collaboration(self, state: AgentState) -> AgentState:
        """Determine if secondary agents should be invoked"""
        # Already set by intent classification for multi_domain queries
        if state.get("requires_collaboration"):
            # Determine which secondary agents to invoke
            query = state["user_query"].lower()
            primary = state["primary_agent"]
            secondary = []

            for agent_name, agent in self.agents.items():
                if agent_name != primary and agent_name != "escalation":
                    can_handle, confidence = agent.can_handle(state)
                    if can_handle and confidence > 0.5:
                        secondary.append(agent_name)

            state["secondary_agents"] = secondary
            logger.info(f"Collaboration needed. Secondary agents: {secondary}")

        return state

    def _should_collaborate(self, state: AgentState) -> bool:
        """Conditional edge: should we invoke secondary agents?"""
        return state.get("requires_collaboration", False) and len(state.get("secondary_agents", [])) > 0

    async def _execute_secondary_agents(self, state: AgentState) -> AgentState:
        """Execute secondary agents for collaborative response"""
        secondary_responses = []

        for agent_name in state.get("secondary_agents", []):
            agent = self.agents[agent_name]

            # Record handoff
            state["agent_handoffs"].append({
                "from_agent": state["active_agent"],
                "to_agent": agent_name,
                "reason": "Multi-domain query collaboration",
                "timestamp": datetime.now().isoformat(),
                "context_passed": {}
            })

            state["active_agent"] = agent_name

            # Record consultation
            if agent_name not in state["consulted_agents"]:
                state["consulted_agents"].append(agent_name)

            logger.info(f"Invoking secondary agent: {agent_name}")

            # Execute
            result = await agent.execute(state)
            secondary_responses.append({
                "agent": agent_name,
                "response": result
            })

        state["secondary_responses"] = secondary_responses
        return state

    def _synthesize_response(self, state: AgentState) -> AgentState:
        """Synthesize responses from multiple agents"""
        primary_response = state.get("primary_response", {})
        secondary_responses = state.get("secondary_responses", [])

        # Combine responses
        combined_text = primary_response.get("text", "")

        if secondary_responses:
            combined_text += "\n\n---\n\n**Additional Information:**\n\n"
            for sec_resp in secondary_responses:
                agent_name = sec_resp["agent"]
                resp_text = sec_resp["response"].get("text", "")
                combined_text += f"**From {agent_name.title()}Agent:**\n{resp_text}\n\n"

        # Combine follow-up options
        all_follow_ups = primary_response.get("follow_up_options", [])
        for sec_resp in secondary_responses:
            all_follow_ups.extend(sec_resp["response"].get("follow_up_options", []))

        # Remove duplicates while preserving order
        seen = set()
        unique_follow_ups = []
        for item in all_follow_ups:
            if item not in seen:
                seen.add(item)
                unique_follow_ups.append(item)

        state["final_response"] = combined_text
        state["follow_up_options"] = unique_follow_ups[:6]  # Limit to 6 options

        logger.info(f"Synthesized response from {len(state['consulted_agents'])} agents")
        return state

    def _check_escalation(self, state: AgentState) -> AgentState:
        """Check if escalation is needed"""
        # Escalation is checked by agents and set in state
        # This node just passes through
        return state

    def _needs_escalation(self, state: AgentState) -> bool:
        """Conditional edge: does this need escalation?"""
        needs = state.get("escalation_required", False)
        if needs:
            logger.info("Escalation required - re-routing to EscalationAgent")
        return needs


# Singleton instance
_orchestrator_instance = None


def get_orchestrator(
    rag_manager=None,
    lambda_client=None,
    account_service=None,
    transaction_service=None,
    analytics_service=None
) -> AgentOrchestrator:
    """Get or create singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator(
            rag_manager=rag_manager,
            lambda_client=lambda_client,
            account_service=account_service,
            transaction_service=transaction_service,
            analytics_service=analytics_service
        )
    return _orchestrator_instance
