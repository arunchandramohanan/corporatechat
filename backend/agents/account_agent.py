"""
Account Agent

Specialized agent for handling account management, balances, limits, and user management.
Uses mock account service to retrieve account data.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from .state import AgentState
from .tools import AgentTools

logger = logging.getLogger(__name__)


class AccountAgent(BaseAgent):
    """Agent specialized in account management and information"""

    def __init__(self, tools: AgentTools, account_service):
        super().__init__(
            name="AccountAgent",
            description="Expert in account management, balances, limits, and settings"
        )
        self.tools_instance = tools
        self.account_service = account_service
        self.tools = ["get_account_info", "get_balance", "update_limits", "add_user"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """Determine if this agent can handle the query"""
        query = state.get("user_query", "").lower()
        intent = state.get("intent", "")

        # Account-related keywords
        account_keywords = [
            "account", "balance", "credit limit", "available credit",
            "spending limit", "authorized user", "add user", "remove user",
            "account info", "account settings", "account status",
            "credit line", "increase limit", "decrease limit",
            "my account", "account summary", "check balance",
            "available funds", "how much credit"
        ]

        if intent == "account_management":
            return True, 0.95

        keyword_matches = sum(1 for keyword in account_keywords if keyword in query)

        if keyword_matches >= 2:
            return True, 0.90
        elif keyword_matches == 1:
            return True, 0.75

        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute account management request"""
        try:
            query = state.get("user_query", "").lower()
            context = state.get("context", {})

            # Determine what account action is needed
            if any(word in query for word in ["balance", "how much", "available"]):
                return await self._handle_balance_inquiry(state)
            elif any(word in query for word in ["limit", "increase", "decrease", "change"]):
                return await self._handle_limit_management(state)
            elif any(word in query for word in ["authorized user", "add user", "remove user"]):
                return await self._handle_user_management(state)
            elif any(word in query for word in ["reward", "point"]):
                return await self._handle_rewards_inquiry(state)
            else:
                return await self._handle_general_account_info(state)

        except Exception as e:
            logger.error(f"Error in AccountAgent execution: {e}")
            state["error"] = str(e)
            return self.format_response(
                text="I apologize, but I encountered an error while retrieving your account information. Please try again or contact support.",
                follow_up_options=["Try again", "Contact support"]
            )

    async def _handle_balance_inquiry(self, state: AgentState) -> Dict[str, Any]:
        """Handle balance and credit inquiries"""
        self.add_step(
            state,
            action="retrieving_balance",
            details="Fetching account balance and credit information",
            tool_used="get_balance"
        )

        balance_result = await self.account_service.get_balance_summary()

        if not balance_result.get("success"):
            return self._handle_service_error(state, "balance information")

        balance_data = balance_result.get("balance_summary", {})

        self.add_step(
            state,
            action="balance_retrieved",
            details=f"Retrieved balance: ${balance_data.get('current_balance', 0):.2f}",
            tool_output=balance_data
        )

        # Use LLM to generate natural response with data
        self.add_step(
            state,
            action="generating_response",
            details="Generating personalized account summary",
            tool_used="call_llm"
        )

        prompt = f"""You are a helpful banking assistant. Generate a concise response about the user's account balance.

IMPORTANT: Use ONLY the Account Data provided below. Do NOT reference or mention any other context or documents.

User Query: {state.get('user_query', '')}

Account Data:
- Current Balance: ${balance_data.get('current_balance', 0):,.2f}
- Credit Limit: ${balance_data.get('credit_limit', 0):,.2f}
- Available Credit: ${balance_data.get('available_credit', 0):,.2f}
- Pending Transactions: ${balance_data.get('pending_transactions', 0):,.2f}
- Available After Pending: ${balance_data.get('available_after_pending', 0):,.2f}
- Credit Utilization: {((balance_data.get('current_balance', 0) / balance_data.get('credit_limit', 1)) * 100):.1f}%

Format as simple HTML table:
<h3>Account Balance</h3>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Detail</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Amount</th>
</tr>
</thead>
<tbody>
[table rows with padding: 8px; border: 1px solid #ddd;]
</tbody>
</table>
<p>Brief summary here.</p>

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=800)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")

        # Update context
        self.update_context(state, {
            "support_category": "account",
            "balance_checked": True,
            "current_balance": balance_data.get('current_balance')
        })

        # Create quote/card summary
        quote = {
            "current_balance": balance_data.get('current_balance', 0),
            "credit_limit": balance_data.get('credit_limit', 0),
            "available_credit": balance_data.get('available_credit', 0),
            "pending_transactions": balance_data.get('pending_transactions', 0)
        }

        return self.format_response(
            text=llm_response,
            follow_up_options=[
                "View recent transactions",
                "Request credit limit increase",
                "Set up balance alerts",
                "Download statement"
            ],
            quote=quote
        )

    async def _handle_limit_management(self, state: AgentState) -> Dict[str, Any]:
        """Handle credit limit and spending limit inquiries/changes"""
        self.add_step(
            state,
            action="reviewing_limits",
            details="Reviewing current spending limits and restrictions"
        )

        account_result = await self.account_service.get_account_info()

        if not account_result.get("success"):
            return self._handle_service_error(state, "account information")

        account = account_result.get("account", {})

        response_text = f"""Here are your current spending limits:

**Credit Limit:** ${account.get('credit_limit', 0):,.2f}
**Per-Transaction Limit:** ${account.get('spending_limit_per_transaction', 0):,.2f}
**Daily Spending Limit:** ${account.get('daily_spending_limit', 0):,.2f}

To request a change to your credit limit, I can help you submit a request. Limit increases typically require:
- Good account standing (current)
- Recent credit review
- Business justification
- Approval from your account administrator

Would you like to proceed with a limit change request?"""

        self.update_context(state, {
            "support_category": "account",
            "limit_inquiry": True
        })

        return self.format_response(
            text=response_text,
            follow_up_options=[
                "Request credit limit increase",
                "Modify per-transaction limit",
                "Adjust daily spending limit",
                "View account details"
            ]
        )

    async def _handle_user_management(self, state: AgentState) -> Dict[str, Any]:
        """Handle authorized user management"""
        self.add_step(
            state,
            action="checking_authorized_users",
            details="Retrieving authorized user information"
        )

        account_result = await self.account_service.get_account_info()

        if not account_result.get("success"):
            return self._handle_service_error(state, "user information")

        account = account_result.get("account", {})
        num_users = account.get("authorized_users", 0)

        response_text = f"""**Authorized Users on Your Account:** {num_users}

You can manage authorized users on your BMO Corporate Card account:

**Adding a User:**
1. User must be approved by account administrator
2. Spending limits can be set individually
3. New card will be issued (7-10 business days)
4. User gets own card number linked to your account

**Removing a User:**
1. Request immediate card cancellation
2. User loses access within 24 hours
3. Any pending transactions still process

Would you like to add or remove an authorized user?"""

        self.update_context(state, {
            "support_category": "account",
            "user_management_inquiry": True
        })

        return self.format_response(
            text=response_text,
            follow_up_options=[
                "Add authorized user",
                "Remove authorized user",
                "View user spending",
                "Set user limits"
            ]
        )

    async def _handle_rewards_inquiry(self, state: AgentState) -> Dict[str, Any]:
        """Handle rewards balance and information"""
        self.add_step(
            state,
            action="retrieving_rewards",
            details="Fetching rewards program information",
            tool_used="get_rewards"
        )

        rewards_result = await self.account_service.get_rewards_info()

        if not rewards_result.get("success"):
            return self._handle_service_error(state, "rewards information")

        rewards = rewards_result.get("rewards", {})

        response_text = f"""**Your BMO Rewards Summary:**

**Points Balance:** {rewards.get('points_balance', 0):,} points
**Estimated Value:** ${rewards.get('points_value', 0):,.2f}

**Points Expiring Soon:**
- {rewards.get('points_expiring', {}).get('amount', 0):,} points expire on {rewards.get('points_expiring', {}).get('expiry_date', 'N/A')}

**Earning Rates:**
- Travel: {rewards.get('earning_rate', {}).get('travel', 'N/A')}
- Dining: {rewards.get('earning_rate', {}).get('dining', 'N/A')}
- Other: {rewards.get('earning_rate', {}).get('other', 'N/A')}

**Redemption Options:** {', '.join(rewards.get('redemption_options', []))}"""

        self.update_context(state, {
            "support_category": "rewards",
            "rewards_balance_checked": True,
            "rewards_balance": rewards.get('points_balance')
        })

        quote = {
            "rewards_points": rewards.get('points_balance', 0),
            "rewards_value": rewards.get('points_value', 0)
        }

        return self.format_response(
            text=response_text,
            follow_up_options=[
                "Redeem rewards",
                "View earning history",
                "Rewards program details",
                "Transfer to partners"
            ],
            quote=quote
        )

    async def _handle_general_account_info(self, state: AgentState) -> Dict[str, Any]:
        """Handle general account information requests"""
        self.add_step(
            state,
            action="retrieving_account_info",
            details="Fetching complete account information",
            tool_used="get_account_info"
        )

        account_result = await self.account_service.get_account_info()

        if not account_result.get("success"):
            return self._handle_service_error(state, "account information")

        account = account_result.get("account", {})

        # Use LLM to generate formatted response
        self.add_step(
            state,
            action="generating_response",
            details="Generating account summary",
            tool_used="call_llm"
        )

        prompt = f"""You are a helpful banking assistant. Present the user's account information in a clear format.

IMPORTANT: Use ONLY the Account Information provided below. Do NOT reference or mention any other context or documents.

User Query: {state.get('user_query', '')}

Account Information:
- Card Type: {account.get('card_type', 'N/A')}
- Card Number: •••• {account.get('card_number_last4', 'N/A')}
- Account Status: {account.get('account_status', 'N/A').title()}
- Credit Limit: ${account.get('credit_limit', 0):,.2f}
- Current Balance: ${account.get('current_balance', 0):,.2f}
- Available Credit: ${account.get('available_credit', 0):,.2f}
- International Transactions: {'Enabled' if account.get('international_enabled') else 'Disabled'}
- Contactless Payments: {'Enabled' if account.get('contactless_enabled') else 'Disabled'}
- Authorized Users: {account.get('authorized_users', 0)}
- Next Statement Date: {account.get('statement_date', 'N/A')}
- Payment Due Date: {account.get('payment_due_date', 'N/A')}

Format as simple HTML table:
<h3>Account Information</h3>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Detail</th>
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Value</th>
</tr>
</thead>
<tbody>
[table rows with padding: 8px; border: 1px solid #ddd;]
</tbody>
</table>

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=1000)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")

        self.update_context(state, {
            "support_category": "account",
            "card_number_last4": account.get('card_number_last4'),
            "account_info_retrieved": True
        })

        return self.format_response(
            text=llm_response,
            follow_up_options=[
                "View recent transactions",
                "Check rewards balance",
                "Update account settings",
                "Download statement"
            ]
        )

    def _handle_service_error(self, state: AgentState, data_type: str) -> Dict[str, Any]:
        """Handle errors from account service"""
        logger.error(f"Account service error retrieving {data_type}")
        return self.format_response(
            text=f"I'm having trouble retrieving your {data_type} right now. This might be a temporary issue. Please try again in a moment or contact support if the problem persists.",
            follow_up_options=["Try again", "Contact support", "Ask another question"]
        )

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """Determine if query should be escalated"""
        query = state.get("user_query", "").lower()

        # Escalate for account disputes or issues
        escalation_triggers = [
            "fraud",
            "unauthorized",
            "dispute",
            "close account",
            "cancel card",
            "complaint"
        ]

        for trigger in escalation_triggers:
            if trigger in query:
                return True, f"Account issue requiring specialist: {trigger}"

        return False, ""
