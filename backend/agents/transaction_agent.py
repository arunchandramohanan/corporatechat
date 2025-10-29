"""
Transaction Agent

Specialized agent for transaction inquiries, disputes, and statement management.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from .state import AgentState
from .tools import AgentTools

logger = logging.getLogger(__name__)


class TransactionAgent(BaseAgent):
    """Agent specialized in transactions and disputes"""

    def __init__(self, tools: AgentTools, transaction_service):
        super().__init__(
            name="TransactionAgent",
            description="Expert in transaction inquiries, disputes, and statements"
        )
        self.tools_instance = tools
        self.transaction_service = transaction_service
        self.tools = ["get_transactions", "search_transactions", "file_dispute", "download_statement"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """Determine if this agent can handle the query"""
        query = state.get("user_query", "").lower()
        intent = state.get("intent", "")

        transaction_keywords = [
            "transaction", "charge", "purchase", "payment", "statement",
            "dispute", "refund", "merchant", "receipt", "download",
            "recent transactions", "transaction history", "spending",
            "what did i spend", "show my", "find transaction"
        ]

        if intent in ["transaction_inquiry", "dispute_filing"]:
            return True, 0.95

        keyword_matches = sum(1 for keyword in transaction_keywords if keyword in query)
        if keyword_matches >= 2:
            return True, 0.90
        elif keyword_matches == 1:
            return True, 0.75

        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute transaction-related request"""
        try:
            query = state.get("user_query", "").lower()

            if any(word in query for word in ["dispute", "fraud", "unauthorized", "didn't make"]):
                return await self._handle_dispute(state)
            elif any(word in query for word in ["statement", "download", "export"]):
                return await self._handle_statement(state)
            elif any(word in query for word in ["find", "search", "look for"]):
                return await self._handle_search(state)
            else:
                return await self._handle_transaction_list(state)

        except Exception as e:
            logger.error(f"Error in TransactionAgent: {e}")
            state["error"] = str(e)
            return self.format_response(
                text="I encountered an error retrieving transaction information. Please try again.",
                follow_up_options=["Try again", "Contact support"]
            )

    async def _handle_transaction_list(self, state: AgentState) -> Dict[str, Any]:
        """Show recent transactions"""
        self.add_step(state, "retrieving_transactions", "Fetching recent transactions", "get_transactions")

        result = await self.transaction_service.get_transactions(limit=10)

        if not result.get("success"):
            return self._error_response("retrieve transactions")

        transactions = result.get("transactions", [])

        # Use LLM to generate formatted response
        self.add_step(
            state,
            action="formatting_transactions",
            details="Generating transaction summary",
            tool_used="call_llm"
        )

        # Prepare transaction data for LLM
        txn_data = "\n".join([
            f"- Date: {t['date'][:10]}, Merchant: {t['merchant_name']}, Amount: ${t['amount']:,.2f} CAD, Category: {t['category']}, Status: {t['status'].title()}"
            for t in transactions
        ])

        prompt = f"""You are a helpful banking assistant. Present recent transactions in a simple HTML table.

IMPORTANT: Use ONLY the Transaction Data provided below. Do NOT reference or use any other context or retrieved documents.

User Query: {state.get('user_query', '')}

Transaction Data:
{txn_data}

Total Amount (Last 10 transactions): ${result.get('total_amount', 0):,.2f} CAD

Format as simple HTML:
<h3>Recent Transactions</h3>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Merchant</th>
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Category</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Amount</th>
<th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Status</th>
</tr>
</thead>
<tbody>
[table rows with padding: 8px; border: 1px solid #ddd;]
</tbody>
</table>
<p>Total: ${result.get('total_amount', 0):,.2f} CAD</p>

Keep it simple and clean."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=1200)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")

        self.update_context(state, {
            "support_category": "transactions",
            "transactions_viewed": True
        })

        return self.format_response(
            llm_response,
            ["View all transactions", "Search for a transaction", "Download statement", "File a dispute"]
        )

    async def _handle_dispute(self, state: AgentState) -> Dict[str, Any]:
        """Handle dispute filing"""
        self.add_step(state, "initiating_dispute", "Starting dispute process")

        response = """I can help you file a dispute for an unauthorized or incorrect charge.

**To file a dispute, I'll need:**
1. Transaction date or merchant name
2. Transaction amount
3. Reason for dispute
4. Any supporting information

**Common dispute reasons:**
- Did not authorize the charge
- Charged incorrect amount
- Product/service not received
- Product defective or not as described
- Duplicate charge

Please provide the transaction details, or I can show you recent transactions to help you find it."""

        self.update_context(state, {
            "support_category": "transactions",
            "dispute_needed": True
        })

        return self.format_response(
            response,
            ["Show recent transactions", "I have transaction details", "Contact support"]
        )

    async def _handle_search(self, state: AgentState) -> Dict[str, Any]:
        """Search for specific transactions"""
        self.add_step(state, "searching_transactions", "Searching transaction history")

        response = """I can help you search for transactions by:

- **Merchant name** (e.g., "Amazon", "Starbucks")
- **Date range** (e.g., "last week", "January")
- **Amount** (e.g., "$50.00", "around $100")
- **Category** (e.g., "Travel", "Dining", "Office Supplies")

What would you like to search for?"""

        return self.format_response(
            response,
            ["Search by merchant", "Search by date", "Search by amount", "Show all transactions"]
        )

    async def _handle_statement(self, state: AgentState) -> Dict[str, Any]:
        """Handle statement download"""
        self.add_step(state, "preparing_statement", "Generating statement download", "download_statement")

        result = await self.transaction_service.download_statement(format="pdf")

        if not result.get("success"):
            return self._error_response("generate statement")

        statement = result.get("statement", {})

        response = f"""**Statement Ready for Download**

**Statement Date:** {statement.get('statement_date')}
**Format:** {statement.get('format', 'PDF').upper()}
**Download Link:** Available for 7 days

Your statement includes all transactions, fees, payments, and rewards earned for the period.

**Also available in:**
- CSV (for Excel/spreadsheet import)
- Excel (XLSX) format"""

        return self.format_response(
            response,
            ["Download PDF", "Download CSV", "Download Excel", "View transactions"]
        )

    def _error_response(self, action: str) -> Dict[str, Any]:
        """Standard error response"""
        return self.format_response(
            f"I'm having trouble trying to {action} right now. Please try again or contact support.",
            ["Try again", "Contact support"]
        )

    def get_follow_up_options(self, state: AgentState) -> List[str]:
        """Generate follow-up options"""
        if state.get("context", {}).get("dispute_needed"):
            return ["Show recent transactions", "I have details", "Contact support"]
        return ["View transactions", "Download statement", "Search transactions"]

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """Check for escalation"""
        query = state.get("user_query", "").lower()
        if any(word in query for word in ["fraud", "stolen", "unauthorized", "scam"]):
            return True, "Potential fraud - requires immediate attention"
        return False, ""
