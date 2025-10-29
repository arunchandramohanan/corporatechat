"""
Analytics Agent

Specialized agent for spending analytics, reports, and budget tracking.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from .state import AgentState
from .tools import AgentTools

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    """Agent specialized in spending analytics and reporting"""

    def __init__(self, tools: AgentTools, analytics_service):
        super().__init__(
            name="AnalyticsAgent",
            description="Expert in spending analytics, trends, and expense reporting"
        )
        self.tools_instance = tools
        self.analytics_service = analytics_service
        self.tools = ["get_spending_analytics", "generate_report", "track_budget"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        """Determine if this agent can handle the query"""
        query = state.get("user_query", "").lower()
        intent = state.get("intent", "")

        analytics_keywords = [
            "analytics", "report", "spending", "trend", "budget",
            "expense", "category", "breakdown", "analysis", "insight",
            "how much spent", "spending by", "monthly spending",
            "track", "compliance", "over budget"
        ]

        if intent == "analytics_request":
            return True, 0.95

        keyword_matches = sum(1 for keyword in analytics_keywords if keyword in query)
        if keyword_matches >= 2:
            return True, 0.90
        elif keyword_matches == 1:
            return True, 0.70

        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute analytics request"""
        try:
            query = state.get("user_query", "").lower()

            if any(word in query for word in ["category", "breakdown", "by category"]):
                return await self._handle_category_analysis(state)
            elif any(word in query for word in ["trend", "over time", "monthly", "weekly"]):
                return await self._handle_trend_analysis(state)
            elif any(word in query for word in ["budget", "on track", "over budget"]):
                return await self._handle_budget_analysis(state)
            elif any(word in query for word in ["report", "expense report", "export"]):
                return await self._handle_report_generation(state)
            else:
                return await self._handle_general_analytics(state)

        except Exception as e:
            logger.error(f"Error in AnalyticsAgent: {e}")
            state["error"] = str(e)
            return self.format_response(
                text="I encountered an error generating analytics. Please try again.",
                follow_up_options=["Try again", "Contact support"]
            )

    async def _handle_category_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Analyze spending by category"""
        self.add_step(state, "analyzing_categories", "Analyzing spending by category", "get_spending_analytics")

        result = await self.analytics_service.get_spending_by_category()

        if not result.get("success"):
            return self._error_response("analyze spending")

        categories = result.get("categories", [])

        # Use LLM to generate formatted response
        self.add_step(
            state,
            action="generating_category_report",
            details="Generating category breakdown report",
            tool_used="call_llm"
        )

        # Prepare data for LLM
        category_data = "\n".join([
            f"- {c['category']}: ${c['total_amount']:,.2f} ({c['percentage']}%) - {c['transaction_count']} transactions"
            for c in categories
        ])

        prompt = f"""You are a helpful banking assistant. Present spending data by category in a simple HTML table.

CRITICAL INSTRUCTIONS:
- Use ONLY the Spending Data provided below
- Do NOT reference any context, documents, or AWS services
- Do NOT mention "provided context", "documents", or anything about missing information
- Just present the spending data in a clean table

User Query: {state.get('user_query', '')}

Spending Data (Last 30 Days):
{category_data}

Total Spending: ${result.get('total_spending', 0):,.2f}
Total Transactions: {result.get('total_transactions', 0)}

Format as simple HTML:
<h3>Spending by Category</h3>
<p>Brief insight here about top category.</p>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Category</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Amount</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">% of Total</th>
<th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Transactions</th>
</tr>
</thead>
<tbody>
[table rows with padding: 8px; border: 1px solid #ddd;]
</tbody>
</table>
<p>Total: ${result.get('total_spending', 0):,.2f} ({result.get('total_transactions', 0)} transactions)</p>

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=1000)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")

        self.update_context(state, {
            "support_category": "analytics",
            "analytics_viewed": True
        })

        return self.format_response(
            llm_response,
            ["View all categories", "See spending trends", "Generate report", "Check budget"]
        )

    async def _handle_trend_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Analyze spending trends"""
        self.add_step(state, "analyzing_trends", "Analyzing spending trends over time")

        result = await self.analytics_service.get_spending_trends(period="monthly", num_periods=6)

        if not result.get("success"):
            return self._error_response("analyze trends")

        trends = result.get("trends", [])
        summary = result.get("summary", {})

        # Build trend rows
        trend_rows = ""
        for t in trends[-3:]:  # Last 3 periods
            trend_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{t['period']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${t['total_amount']:,.2f}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{t['transaction_count']}</td>
            </tr>"""

        trend_direction = summary.get('trend_direction', 'stable').title()

        response = f"""<h3>Spending Trends (Last 6 Months)</h3>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Period</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Total Spent</th>
<th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Transactions</th>
</tr>
</thead>
<tbody>
{trend_rows}
</tbody>
</table>
<p><strong>Trend Analysis:</strong></p>
<ul>
<li>Direction: {trend_direction}</li>
<li>Change: {summary.get('change_percentage', 0)}%</li>
<li>Highest Period: {summary.get('highest_period', 'N/A')}</li>
<li>Lowest Period: {summary.get('lowest_period', 'N/A')}</li>
</ul>
<p>Your spending is {'increasing' if summary.get('trend_direction') == 'increasing' else 'decreasing'} compared to previous months.</p>"""

        return self.format_response(
            response,
            ["View category breakdown", "Generate detailed report", "Check budget status"]
        )

    async def _handle_budget_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Analyze budget vs actual"""
        self.add_step(state, "analyzing_budget", "Analyzing budget vs actual spending")

        result = await self.analytics_service.get_budget_analysis(monthly_budget=10000.00)

        if not result.get("success"):
            return self._error_response("analyze budget")

        budget = result.get("budget", {})
        projections = result.get("projections", {})

        status = budget.get('status')
        status_text = "On Track" if status == 'on_track' else "Over Budget"
        percentage = budget.get('percentage_used', 0)

        response = f"""<h3>Budget Analysis - {result.get('timeline', {}).get('period', 'October 2025')}</h3>
<p><strong>Status:</strong> {status_text} ({percentage}% of budget used)</p>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Metric</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Amount</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Monthly Budget</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${budget.get('monthly_budget', 0):,.2f}</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Amount Spent</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${budget.get('current_spending', 0):,.2f}</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Remaining Budget</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${budget.get('remaining_budget', 0):,.2f}</td>
</tr>
</tbody>
</table>
<p><strong>Projections:</strong></p>
<ul>
<li>Projected Month-End: ${projections.get('projected_month_end', 0):,.2f}</li>
<li>Over/Under Budget: ${projections.get('projected_over_under', 0):,.2f}</li>
<li>Daily Budget Target: ${projections.get('daily_budget_target', 0):,.2f}</li>
<li>Current Daily Average: ${projections.get('current_daily_average', 0):,.2f}</li>
</ul>
<p><strong>Recommendation:</strong> {'Limit daily spending to $' + f"{projections.get('recommended_daily_spend', 0):,.2f}" + ' to stay on budget.' if budget.get('remaining_budget', 0) >= 0 else 'You are currently over budget. Review your spending and reduce discretionary expenses.'}</p>"""

        return self.format_response(
            response,
            ["View spending details", "Set budget alerts", "Generate compliance report"]
        )

    async def _handle_report_generation(self, state: AgentState) -> Dict[str, Any]:
        """Generate expense report"""
        self.add_step(state, "generating_report", "Generating expense report", "generate_report")

        result = await self.analytics_service.generate_expense_report(format="export")

        if not result.get("success"):
            return self._error_response("generate report")

        report = result.get("report", {})
        period = report.get('period', {})
        summary = report.get('summary', {})

        response = f"""<h3>Expense Report Generated</h3>
<p><strong>Report ID:</strong> {report.get('report_id')}</p>
<p><strong>Period:</strong> {period.get('start_date')} to {period.get('end_date')}</p>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Summary Item</th>
<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Value</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Total Spending</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${summary.get('total_spending', 0):,.2f}</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Total Transactions</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{summary.get('total_transactions', 0)}</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Categories</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{summary.get('categories_count', 0)}</td>
</tr>
</tbody>
</table>
<p><strong>Report Includes:</strong></p>
<ul>
<li>Category breakdown with percentages</li>
<li>Top merchants and transaction details</li>
<li>Trend analysis and insights</li>
<li>Export-ready format (Excel/CSV)</li>
</ul>
<p><strong>Download:</strong> {report.get('download_url', 'Available in dashboard')}</p>"""

        return self.format_response(
            response,
            ["Download report", "View details", "Generate another report"]
        )

    async def _handle_general_analytics(self, state: AgentState) -> Dict[str, Any]:
        """General analytics overview"""
        # Use LLM to generate formatted response
        self.add_step(
            state,
            action="generating_analytics_menu",
            details="Generating analytics options menu",
            tool_used="call_llm"
        )

        prompt = """You are a helpful banking assistant. Present the available analytics options in a simple HTML table.

CRITICAL INSTRUCTIONS:
- Use ONLY the analytics options listed below
- Do NOT reference any context, documents, or AWS services
- Do NOT mention "provided context", "documents", or anything about missing information
- Just present the analytics options in a clean table

Available Analytics:
1. Category Breakdown - See spending by category
2. Spending Trends - Track changes over time
3. Budget Analysis - Compare actual vs budget
4. Expense Reports - Generate detailed reports
5. Compliance Tracking - Monitor policy limits

Format as simple HTML:
<h3>Available Analytics</h3>
<p>What would you like to analyze?</p>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<thead>
<tr style="background-color: #f0f0f0;">
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Analytics Type</th>
<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Description</th>
</tr>
</thead>
<tbody>
[table rows with padding: 8px; border: 1px solid #ddd;]
</tbody>
</table>

IMPORTANT: USE COMPACT VERTICAL SPACING - minimize blank lines between elements. Keep response dense with minimal whitespace."""

        llm_result = await self.tools_instance.call_llm(prompt, max_tokens=800)
        llm_response = llm_result.get("response", "I apologize, but I encountered an error generating the response.")

        return self.format_response(
            llm_response,
            ["Category breakdown", "Spending trends", "Budget analysis", "Generate report"]
        )

    def _error_response(self, action: str) -> Dict[str, Any]:
        """Standard error response"""
        return self.format_response(
            f"I'm having trouble trying to {action} right now. Please try again.",
            ["Try again", "Contact support"]
        )

    def get_follow_up_options(self, state: AgentState) -> List[str]:
        """Generate follow-up options"""
        return ["Category breakdown", "Spending trends", "Budget analysis", "Generate report"]

    def should_escalate(self, state: AgentState) -> tuple[bool, str]:
        """Check for escalation"""
        return False, ""
