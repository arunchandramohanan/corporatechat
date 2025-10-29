"""
Escalation Agent

Specialized agent for handling complex issues that require human intervention.
Creates escalation tickets and routes to appropriate support channels.
"""

from typing import Dict, Any, List
import logging
import random
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from .state import AgentState
from .tools import AgentTools

logger = logging.getLogger(__name__)


class EscalationAgent(BaseAgent):
    """Agent specialized in escalation and human handoff"""

    def __init__(self, tools: AgentTools):
        super().__init__(
            name="EscalationAgent",
            description="Expert in escalations, complaints, and complex issue resolution"
        )
        self.tools_instance = tools
        self.tools = ["create_ticket", "assess_priority", "route_to_specialist"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """Determine if this agent can handle the query"""
        query = state.get("user_query", "").lower()
        intent = state.get("intent", "")

        escalation_keywords = [
            "escalate", "manager", "supervisor", "complaint", "speak to human",
            "not satisfied", "unhappy", "frustrated", "this is ridiculous",
            "want to cancel", "close account", "legal", "lawyer",
            "fraud", "stolen card", "emergency", "urgent", "immediately"
        ]

        if intent == "escalation":
            return True, 0.95

        # Check if other agents marked for escalation
        if state.get("escalation_required", False):
            return True, 1.0

        keyword_matches = sum(1 for keyword in escalation_keywords if keyword in query)
        if keyword_matches >= 2:
            return True, 0.90
        elif keyword_matches == 1:
            return True, 0.80

        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute escalation handling"""
        try:
            query = state.get("user_query", "").lower()
            context = state.get("context", {})

            # Check if we're in the question-gathering phase or ready to create ticket
            escalation_phase = context.get("escalation_phase", "initial")

            # Check if user wants to skip questions
            skip_keywords = ["skip", "speak to someone now", "immediate", "now", "don't want to answer"]
            wants_to_skip = any(keyword in query for keyword in skip_keywords)

            if escalation_phase == "initial" and not wants_to_skip:
                # First interaction - ask clarifying questions
                return await self._gather_information(state)
            elif escalation_phase == "gathering_info" or wants_to_skip:
                # User has provided answers or wants to skip - create the ticket
                return await self._create_ticket_with_info(state)
            else:
                # Fallback to direct ticket creation
                return await self._create_ticket_with_info(state)

        except Exception as e:
            logger.error(f"Error in EscalationAgent: {e}")
            state["error"] = str(e)
            return self.format_response(
                text="I apologize for the inconvenience. Let me connect you with a support specialist immediately. Please hold while I transfer your request.",
                follow_up_options=["Contact support now", "Try again later"]
            )

    async def _gather_information(self, state: AgentState) -> Dict[str, Any]:
        """Ask clarifying questions before creating escalation ticket"""
        query = state.get("user_query", "")
        context = state.get("context", {})

        # Determine escalation type and priority
        escalation_type, priority = self._assess_escalation(query.lower(), context)

        self.add_step(
            state,
            action="assessing_issue",
            details=f"Classified as {escalation_type} escalation with {priority} priority"
        )

        # Get relevant questions for this escalation type
        questions = self._get_clarifying_questions(escalation_type)

        self.add_step(
            state,
            action="gathering_information",
            details=f"Requesting {len(questions)} clarifying details before escalation"
        )

        # Build question response
        response = await self._build_question_response(escalation_type, priority, questions, state)

        # Update context to track that we're gathering info
        self.update_context(state, {
            "escalation_phase": "gathering_info",
            "escalation_type": escalation_type,
            "priority": priority,
            "support_category": "escalation"
        })

        # Mark escalation as handled (questions asked) to prevent recursion
        state["escalation_required"] = False

        return self.format_response(
            text=response,
            follow_up_options=["I'd rather speak to someone now", "Skip questions and escalate"],
            quote=None
        )

    async def _create_ticket_with_info(self, state: AgentState) -> Dict[str, Any]:
        """Create escalation ticket with gathered information"""
        query = state.get("user_query", "")
        context = state.get("context", {})

        # Get escalation details from context
        escalation_type = context.get("escalation_type", "general_escalation")
        priority = context.get("priority", "medium")

        self.add_step(
            state,
            action="processing_information",
            details="Processing provided information for escalation"
        )

        # Create escalation ticket with enriched context
        ticket = self._create_escalation_ticket(
            query=query,
            escalation_type=escalation_type,
            priority=priority,
            context=context,
            consulted_agents=state.get("consulted_agents", [])
        )

        self.add_step(
            state,
            action="ticket_created",
            details=f"Created escalation ticket {ticket['ticket_id']}",
            tool_used="create_ticket",
            tool_output=ticket
        )

        # Build escalation response using LLM
        self.add_step(
            state,
            action="generating_escalation_response",
            details="Generating escalation confirmation",
            tool_used="call_llm"
        )

        response = await self._build_escalation_response(ticket, escalation_type, priority, state)

        # Update context - clear the gathering phase
        self.update_context(state, {
            "support_category": "escalation",
            "escalation_ticket": ticket['ticket_id'],
            "escalation_type": escalation_type,
            "priority": priority,
            "escalation_phase": "completed"
        })

        # Mark escalation as handled
        state["escalation_required"] = False

        return self.format_response(
            text=response,
            follow_up_options=self._get_escalation_follow_ups(escalation_type),
            quote=None
        )

    def _get_clarifying_questions(self, escalation_type: str) -> List[str]:
        """Get relevant clarifying questions based on escalation type"""
        questions = {
            "fraud_security": [
                "When did you first notice the suspicious activity?",
                "Which specific transaction(s) or charges are you concerned about?",
                "Have you authorized anyone else to use your card recently?",
                "Do you still have possession of your physical card?",
                "Have you noticed any other unusual account activity?"
            ],
            "account_closure": [
                "What is your primary reason for wanting to close your account?",
                "Are you aware of any outstanding balance or pending transactions?",
                "Have you explored our retention offers or alternative solutions?",
                "Would you like to transfer or redeem your rewards points first?",
                "Is there anything we can do to address your concerns?"
            ],
            "complaint": [
                "Can you describe the specific issue or experience you're unhappy with?",
                "When did this issue occur?",
                "Have you contacted us about this before? If so, what happened?",
                "What outcome or resolution are you hoping for?",
                "Is there any documentation (emails, receipts, etc.) related to this issue?"
            ],
            "technical_issue": [
                "What specifically is not working or what error are you experiencing?",
                "When did you first encounter this problem?",
                "What device and browser/app are you using?",
                "What have you already tried to resolve this?",
                "Are you receiving any error messages? If so, what do they say?"
            ],
            "general_escalation": [
                "Can you describe the nature of your concern?",
                "What has prompted you to request an escalation?",
                "Have you tried to resolve this issue already? What happened?",
                "How urgent is this matter for you?",
                "What would be a satisfactory resolution for you?"
            ]
        }
        return questions.get(escalation_type, questions["general_escalation"])

    async def _build_question_response(
        self,
        escalation_type: str,
        priority: str,
        questions: List[str],
        state: AgentState
    ) -> str:
        """Build a response that asks clarifying questions"""

        # Create formatted question list
        questions_formatted = "\n".join([f"{i}. {q}" for i, q in enumerate(questions, 1)])

        escalation_names = {
            "fraud_security": "fraud or security concern",
            "account_closure": "account closure request",
            "complaint": "complaint",
            "technical_issue": "technical issue",
            "general_escalation": "concern"
        }

        issue_name = escalation_names.get(escalation_type, "issue")

        prompt = f"""You are a helpful banking assistant handling an escalation request. The user has requested to escalate their {issue_name}.

Priority Level: {priority.upper()}

IMPORTANT: Respond ONLY with the banking customer service message. Do NOT acknowledge, mention, or reference any technical context, AWS services, or irrelevant information. Focus exclusively on the banking escalation scenario.

Before creating an escalation ticket, you need to gather some information to ensure the right specialist handles their case effectively.

Create a warm, professional response that:
1. Acknowledges their request to escalate
2. Explains that you need a few details to route them to the right specialist team
3. Presents these {len(questions)} questions in a clear, numbered format
4. Reassures them this will help expedite their case
5. Keeps a helpful, empathetic tone

Questions to ask:
{questions_formatted}

Format the response with:
- A brief acknowledgment (2-3 sentences)
- Short explanation of why you're asking (1-2 sentences)
- The numbered questions clearly formatted
- A reassuring closing statement (1-2 sentences)

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace.

OUTPUT ONLY THE CUSTOMER-FACING MESSAGE. Do not include any meta-commentary, context acknowledgments, or technical notes."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=800)
        llm_response = llm_result.get("response", "I understand you'd like to escalate this. To help you best, could you please provide some additional details?")
        return llm_response

    def _assess_escalation(self, query: str, context: Dict[str, Any]) -> tuple[str, str]:
        """
        Assess the type and priority of escalation.

        Returns:
            (escalation_type, priority)
        """
        query_lower = query.lower()

        # Check for emergency/fraud
        if any(word in query_lower for word in ["fraud", "stolen", "unauthorized", "scam", "emergency"]):
            return "fraud_security", "critical"

        # Check for account closure
        if any(word in query_lower for word in ["close account", "cancel", "terminate"]):
            return "account_closure", "high"

        # Check for complaints
        if any(word in query_lower for word in ["complaint", "unsatisfied", "unhappy", "frustrated"]):
            return "complaint", "medium"

        # Check for complex requests
        if any(word in query_lower for word in ["manager", "supervisor", "speak to human"]):
            return "general_escalation", "medium"

        # Check for technical issues
        if any(word in query_lower for word in ["can't access", "locked out", "not working"]):
            return "technical_issue", "high"

        # Default
        return "general_escalation", "medium"

    def _create_escalation_ticket(
        self,
        query: str,
        escalation_type: str,
        priority: str,
        context: Dict[str, Any],
        consulted_agents: List[str]
    ) -> Dict[str, Any]:
        """Create an escalation ticket"""
        ticket_id = f"ESC-{datetime.now().year}{random.randint(100000, 999999)}"
        case_number = f"CASE-{random.randint(10000, 99999)}"

        # Calculate SLA based on priority
        sla_hours = {
            "critical": 2,
            "high": 24,
            "medium": 48,
            "low": 72
        }

        response_time = timedelta(hours=sla_hours.get(priority, 48))
        expected_response = (datetime.now() + response_time).isoformat()

        # Check if clarifying information was gathered
        info_gathered = context.get("escalation_phase") == "gathering_info"

        ticket = {
            "ticket_id": ticket_id,
            "case_number": case_number,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "priority": priority,
            "escalation_type": escalation_type,
            "issue_description": query,
            "context_summary": self._summarize_context(context),
            "clarifying_info_provided": info_gathered,
            "consulted_agents": consulted_agents,
            "assigned_to": self._route_to_specialist(escalation_type),
            "expected_response_by": expected_response,
            "sla_hours": sla_hours.get(priority, 48),
            "contact_method": "email",  # Could be enhanced to ask user preference
            "next_steps": self._get_next_steps(escalation_type, priority)
        }

        logger.info(f"Created escalation ticket {ticket_id} - Type: {escalation_type}, Priority: {priority}")

        return ticket

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create a summary of the conversation context for the ticket"""
        summary_parts = []

        if context.get("support_category"):
            summary_parts.append(f"Category: {context['support_category']}")

        if context.get("card_number_last4"):
            summary_parts.append(f"Card: ••••{context['card_number_last4']}")

        if context.get("transaction_details"):
            summary_parts.append("Transaction inquiry involved")

        if context.get("dispute_needed"):
            summary_parts.append("Dispute filing attempted")

        return " | ".join(summary_parts) if summary_parts else "General inquiry"

    def _route_to_specialist(self, escalation_type: str) -> str:
        """Determine which specialist team should handle this"""
        routing_map = {
            "fraud_security": "Fraud Prevention Team",
            "account_closure": "Account Services Team",
            "complaint": "Customer Relations Team",
            "technical_issue": "Technical Support Team",
            "general_escalation": "Senior Support Team"
        }
        return routing_map.get(escalation_type, "Customer Service Team")

    def _get_next_steps(self, escalation_type: str, priority: str) -> List[str]:
        """Get next steps based on escalation type"""
        if escalation_type == "fraud_security":
            return [
                "Card has been flagged for review",
                "Fraud specialist will contact you within 2 hours",
                "Do not use the card until cleared",
                "Monitor your account for suspicious activity",
                "Keep all relevant documentation"
            ]
        elif escalation_type == "account_closure":
            return [
                "Account closure request received",
                "Specialist will verify your identity",
                "Outstanding balance must be cleared",
                "Rewards points will be forfeited unless redeemed",
                "Final confirmation required before processing"
            ]
        elif escalation_type == "complaint":
            return [
                "Your feedback has been documented",
                "Customer Relations team will review",
                "You will receive a detailed response",
                "Case manager assigned to your issue",
                "Follow-up within 24-48 hours"
            ]
        else:
            return [
                "Your issue has been escalated",
                "A specialist will review your case",
                "You will receive email updates",
                "Expected response time provided below",
                "Reference your case number for follow-up"
            ]

    async def _build_escalation_response(
        self,
        ticket: Dict[str, Any],
        escalation_type: str,
        priority: str,
        state: AgentState
    ) -> str:
        """Build the escalation response message using LLM"""

        # Prepare next steps
        next_steps_text = "\n".join([f"{i}. {step}" for i, step in enumerate(ticket['next_steps'], 1)])

        prompt = f"""You are a helpful banking assistant handling an escalation. Create an empathetic, professional response.

IMPORTANT: Respond ONLY with the customer-facing escalation confirmation message. Do NOT acknowledge, mention, or reference any technical context, AWS services, or irrelevant information. Focus exclusively on the banking escalation.

Escalation Details:
- Priority: {priority.upper()}
- Case Number: {ticket['case_number']}
- Ticket ID: {ticket['ticket_id']}
- Assigned To: {ticket['assigned_to']}
- Expected Response: Within {ticket['sla_hours']} hours
- Status: {ticket['status'].title()}
- Escalation Type: {escalation_type}

Next Steps:
{next_steps_text}

Create a response with an HTML table showing the escalation details:
- Blue header (#0066cc)
- Rows for: Priority (with emoji 🔴/🟠/🟡), Case Number, Ticket ID, Assigned To, Expected Response, Status
- Professional styling
- Include the Next Steps as a numbered list after the table
- Add an empathetic closing message acknowledging the importance and reassuring the customer

Be warm, professional, and reassuring.

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace.

OUTPUT ONLY THE CUSTOMER-FACING MESSAGE. Do not include any meta-commentary or context acknowledgments."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=1000)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")
        return llm_response

    def _get_escalation_follow_ups(self, escalation_type: str) -> List[str]:
        """Get follow-up options for escalations"""
        if escalation_type == "fraud_security":
            return [
                "I have more information to add",
                "Check escalation status",
                "Speak with fraud team now"
            ]
        else:
            return [
                "Add more details to my case",
                "Check escalation status",
                "Contact me another way",
                "I need immediate help"
            ]

    def get_follow_up_options(self, state: AgentState) -> List[str]:
        """Generate follow-up options"""
        return [
            "Check status of my escalation",
            "Add more information",
            "Speak with specialist now"
        ]

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """This agent IS the escalation, so always returns False"""
        return False, ""
