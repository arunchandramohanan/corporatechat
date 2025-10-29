"""
Mock Analytics Service

Simulates spending analytics and reporting capabilities.
In production, this would integrate with real analytics/BI systems.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import random
import logging

logger = logging.getLogger(__name__)


class MockAnalyticsService:
    """Mock service for spending analytics and reports"""

    def __init__(self, transaction_service=None):
        """
        Initialize analytics service.

        Args:
            transaction_service: MockTransactionService instance for data
        """
        self.transaction_service = transaction_service

    async def get_spending_by_category(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get spending breakdown by category.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Category spending data
        """
        try:
            # Set defaults
            if not end_date:
                end_date = datetime.now().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).isoformat()

            # Get transactions
            if self.transaction_service:
                result = await self.transaction_service.get_transactions(
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000
                )
                transactions = result.get("transactions", [])
            else:
                transactions = []

            # Aggregate by category
            category_totals = defaultdict(float)
            category_counts = defaultdict(int)

            for txn in transactions:
                category = txn.get("category", "Other")
                amount = txn.get("amount", 0)
                category_totals[category] += amount
                category_counts[category] += 1

            # Format results
            categories = [
                {
                    "category": cat,
                    "total_amount": round(amount, 2),
                    "transaction_count": category_counts[cat],
                    "average_transaction": round(amount / category_counts[cat], 2),
                    "percentage": 0  # Will calculate below
                }
                for cat, amount in category_totals.items()
            ]

            # Calculate percentages
            total_spending = sum(c["total_amount"] for c in categories)
            for cat in categories:
                cat["percentage"] = round((cat["total_amount"] / total_spending * 100), 1) if total_spending > 0 else 0

            # Sort by amount descending
            categories.sort(key=lambda x: x["total_amount"], reverse=True)

            logger.info(f"Analyzed spending across {len(categories)} categories")

            return {
                "success": True,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "categories": categories,
                "total_spending": round(total_spending, 2),
                "total_transactions": sum(category_counts.values())
            }
        except Exception as e:
            logger.error(f"Error analyzing spending by category: {e}")
            return {"success": False, "error": str(e)}

    async def get_spending_trends(
        self,
        period: str = "monthly",  # daily, weekly, monthly
        num_periods: int = 6
    ) -> Dict[str, Any]:
        """
        Get spending trends over time.

        Args:
            period: Time period granularity
            num_periods: Number of periods to analyze

        Returns:
            Trend data
        """
        try:
            trends = []
            current_date = datetime.now()

            # Generate trend data based on period
            for i in range(num_periods):
                if period == "monthly":
                    period_date = current_date - timedelta(days=30 * i)
                    period_label = period_date.strftime("%B %Y")
                    # Mock data with some variation
                    base_amount = 4500
                    amount = base_amount + random.uniform(-1000, 1500)
                elif period == "weekly":
                    period_date = current_date - timedelta(weeks=i)
                    period_label = f"Week of {period_date.strftime('%b %d')}"
                    base_amount = 1100
                    amount = base_amount + random.uniform(-300, 400)
                else:  # daily
                    period_date = current_date - timedelta(days=i)
                    period_label = period_date.strftime("%b %d")
                    base_amount = 150
                    amount = base_amount + random.uniform(-50, 100)

                trends.append({
                    "period": period_label,
                    "date": period_date.date().isoformat(),
                    "total_amount": round(amount, 2),
                    "transaction_count": random.randint(5, 25),
                    "average_transaction": round(amount / random.randint(5, 25), 2)
                })

            # Reverse to show chronological order
            trends.reverse()

            # Calculate trend direction
            if len(trends) >= 2:
                recent_avg = sum(t["total_amount"] for t in trends[-3:]) / 3
                previous_avg = sum(t["total_amount"] for t in trends[:3]) / 3
                trend_direction = "increasing" if recent_avg > previous_avg else "decreasing"
                trend_percentage = round(abs((recent_avg - previous_avg) / previous_avg * 100), 1)
            else:
                trend_direction = "stable"
                trend_percentage = 0

            logger.info(f"Generated {period} trends for {num_periods} periods")

            return {
                "success": True,
                "period_type": period,
                "trends": trends,
                "summary": {
                    "trend_direction": trend_direction,
                    "change_percentage": trend_percentage,
                    "highest_period": max(trends, key=lambda x: x["total_amount"])["period"],
                    "lowest_period": min(trends, key=lambda x: x["total_amount"])["period"]
                }
            }
        except Exception as e:
            logger.error(f"Error generating spending trends: {e}")
            return {"success": False, "error": str(e)}

    async def get_budget_analysis(
        self,
        monthly_budget: float = 10000.00
    ) -> Dict[str, Any]:
        """
        Analyze spending vs budget.

        Args:
            monthly_budget: Monthly budget target

        Returns:
            Budget analysis
        """
        try:
            # Get current month spending
            start_of_month = datetime.now().replace(day=1).isoformat()
            end_of_month = datetime.now().isoformat()

            if self.transaction_service:
                result = await self.transaction_service.get_transactions(
                    start_date=start_of_month,
                    end_date=end_of_month,
                    limit=1000
                )
                transactions = result.get("transactions", [])
                current_spending = sum(t["amount"] for t in transactions)
            else:
                current_spending = 4850.75  # Mock amount

            # Calculate metrics
            days_in_month = 30
            current_day = datetime.now().day
            days_remaining = days_in_month - current_day

            daily_budget = monthly_budget / days_in_month
            current_daily_avg = current_spending / current_day if current_day > 0 else 0
            projected_spending = current_spending + (current_daily_avg * days_remaining)

            remaining_budget = monthly_budget - current_spending
            budget_status = "on_track" if projected_spending <= monthly_budget else "over_budget"

            logger.info(f"Budget analysis: ${current_spending:.2f} / ${monthly_budget:.2f}")

            return {
                "success": True,
                "budget": {
                    "monthly_budget": monthly_budget,
                    "current_spending": round(current_spending, 2),
                    "remaining_budget": round(remaining_budget, 2),
                    "percentage_used": round((current_spending / monthly_budget * 100), 1),
                    "status": budget_status
                },
                "projections": {
                    "projected_month_end": round(projected_spending, 2),
                    "projected_over_under": round(projected_spending - monthly_budget, 2),
                    "daily_budget_target": round(daily_budget, 2),
                    "current_daily_average": round(current_daily_avg, 2),
                    "recommended_daily_spend": round(remaining_budget / days_remaining, 2) if days_remaining > 0 else 0
                },
                "timeline": {
                    "days_elapsed": current_day,
                    "days_remaining": days_remaining,
                    "period": datetime.now().strftime("%B %Y")
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing budget: {e}")
            return {"success": False, "error": str(e)}

    async def generate_expense_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = "summary"
    ) -> Dict[str, Any]:
        """
        Generate expense report.

        Args:
            start_date: Report start date
            end_date: Report end date
            format: Report format (summary, detailed, export)

        Returns:
            Expense report data
        """
        try:
            # Get spending by category
            category_result = await self.get_spending_by_category(start_date, end_date)

            if not category_result.get("success"):
                return category_result

            # Get trends
            trend_result = await self.get_spending_trends(period="monthly", num_periods=3)

            report = {
                "report_id": f"RPT-{datetime.now().year}{random.randint(10000, 99999)}",
                "generated_at": datetime.now().isoformat(),
                "period": category_result["period"],
                "summary": {
                    "total_spending": category_result["total_spending"],
                    "total_transactions": category_result["total_transactions"],
                    "average_transaction": round(
                        category_result["total_spending"] / category_result["total_transactions"], 2
                    ) if category_result["total_transactions"] > 0 else 0,
                    "categories_count": len(category_result["categories"])
                },
                "category_breakdown": category_result["categories"],
                "top_merchants": [
                    {"merchant": "Air Canada", "amount": 1245.00, "count": 2},
                    {"merchant": "Microsoft Azure", "amount": 450.00, "count": 1},
                    {"merchant": "Hilton Hotels", "amount": 389.50, "count": 1}
                ],
                "trend_analysis": trend_result.get("summary", {}) if trend_result.get("success") else {}
            }

            if format == "export":
                report["download_url"] = f"/api/reports/download/{report['report_id']}.xlsx"
                report["expires_at"] = (datetime.now() + timedelta(days=7)).isoformat()

            logger.info(f"Generated expense report {report['report_id']}")

            return {
                "success": True,
                "report": report
            }
        except Exception as e:
            logger.error(f"Error generating expense report: {e}")
            return {"success": False, "error": str(e)}

    async def get_compliance_report(
        self,
        policy_limits: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for policy violations.

        Args:
            policy_limits: Dictionary of category limits

        Returns:
            Compliance report
        """
        try:
            # Default policy limits
            if not policy_limits:
                policy_limits = {
                    "Travel": 3000.00,
                    "Dining": 500.00,
                    "Office Supplies": 750.00,
                    "Software": 1000.00
                }

            # Get spending by category
            category_result = await self.get_spending_by_category()

            if not category_result.get("success"):
                return category_result

            violations = []
            compliant = []

            for cat_data in category_result["categories"]:
                category = cat_data["category"]
                amount = cat_data["total_amount"]

                if category in policy_limits:
                    limit = policy_limits[category]
                    if amount > limit:
                        violations.append({
                            "category": category,
                            "limit": limit,
                            "actual": amount,
                            "over_by": round(amount - limit, 2),
                            "percentage_over": round(((amount - limit) / limit * 100), 1)
                        })
                    else:
                        compliant.append({
                            "category": category,
                            "limit": limit,
                            "actual": amount,
                            "remaining": round(limit - amount, 2)
                        })

            logger.info(f"Compliance check: {len(violations)} violations found")

            return {
                "success": True,
                "compliance_status": "non_compliant" if violations else "compliant",
                "violations": violations,
                "compliant_categories": compliant,
                "summary": {
                    "total_violations": len(violations),
                    "total_over_limit": round(sum(v["over_by"] for v in violations), 2),
                    "requires_approval": len(violations) > 0
                }
            }
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_analytics_service_instance = None


def get_analytics_service(transaction_service=None) -> MockAnalyticsService:
    """Get singleton instance of MockAnalyticsService"""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = MockAnalyticsService(transaction_service)
    return _analytics_service_instance
