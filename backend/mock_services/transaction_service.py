"""
Mock Transaction Service

Simulates transaction data API and dispute filing.
In production, this would integrate with real banking transaction systems.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class MockTransactionService:
    """Mock service for transaction data and management"""

    def __init__(self):
        """Initialize mock transaction data"""
        self.transactions = self._generate_mock_transactions()
        self.disputes = []

    def _generate_mock_transactions(self) -> List[Dict[str, Any]]:
        """Generate realistic mock transactions"""
        merchants = [
            ("Amazon Canada", "Online Shopping", 156.43),
            ("Starbucks", "Dining", 12.75),
            ("Shell Gas Station", "Fuel", 85.20),
            ("Air Canada", "Travel", 1245.00),
            ("Hilton Hotels", "Travel", 389.50),
            ("Office Depot", "Office Supplies", 234.67),
            ("Uber", "Transportation", 45.30),
            ("Rogers", "Telecom", 125.99),
            ("Tim Hortons", "Dining", 8.95),
            ("Best Buy", "Electronics", 567.89),
            ("Staples", "Office Supplies", 98.45),
            ("Delta Hotels", "Travel", 295.00),
            ("Esso", "Fuel", 72.50),
            ("LinkedIn Premium", "Software", 39.99),
            ("Microsoft Azure", "Cloud Services", 450.00),
        ]

        transactions = []
        base_date = datetime.now()

        for i in range(30):  # Generate 30 transactions
            days_ago = i
            merchant, category, base_amount = random.choice(merchants)

            transaction = {
                "transaction_id": f"TXN-{base_date.year}{random.randint(100000, 999999)}",
                "date": (base_date - timedelta(days=days_ago)).isoformat(),
                "merchant_name": merchant,
                "category": category,
                "amount": round(base_amount * random.uniform(0.8, 1.2), 2),
                "currency": "CAD",
                "status": "posted" if days_ago > 2 else "pending",
                "card_last4": "8247",
                "merchant_category_code": "5411",
                "location": random.choice(["Toronto, ON", "Vancouver, BC", "Montreal, QC", "Online"]),
                "is_international": random.random() < 0.1,
                "rewards_earned": random.randint(10, 100)
            }
            transactions.append(transaction)

        return sorted(transactions, key=lambda x: x["date"], reverse=True)

    async def get_transactions(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transaction history.

        Args:
            account_id: Account identifier
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of transactions to return
            category: Filter by category

        Returns:
            Transaction list
        """
        try:
            filtered_transactions = self.transactions.copy()

            # Apply filters
            if start_date:
                filtered_transactions = [
                    t for t in filtered_transactions
                    if t["date"] >= start_date
                ]

            if end_date:
                filtered_transactions = [
                    t for t in filtered_transactions
                    if t["date"] <= end_date
                ]

            if category:
                filtered_transactions = [
                    t for t in filtered_transactions
                    if t["category"].lower() == category.lower()
                ]

            # Apply limit
            filtered_transactions = filtered_transactions[:limit]

            logger.info(f"Retrieved {len(filtered_transactions)} transactions")

            return {
                "success": True,
                "transactions": filtered_transactions,
                "total_count": len(filtered_transactions),
                "total_amount": sum(t["amount"] for t in filtered_transactions)
            }
        except Exception as e:
            logger.error(f"Error retrieving transactions: {e}")
            return {
                "success": False,
                "error": str(e),
                "transactions": []
            }

    async def get_transaction_by_id(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get details for a specific transaction.

        Args:
            transaction_id: Transaction identifier

        Returns:
            Transaction details
        """
        try:
            transaction = next(
                (t for t in self.transactions if t["transaction_id"] == transaction_id),
                None
            )

            if not transaction:
                return {"success": False, "error": "Transaction not found"}

            return {
                "success": True,
                "transaction": transaction
            }
        except Exception as e:
            logger.error(f"Error retrieving transaction: {e}")
            return {"success": False, "error": str(e)}

    async def search_transactions(
        self,
        merchant_name: Optional[str] = None,
        amount: Optional[float] = None,
        amount_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Search transactions by criteria.

        Args:
            merchant_name: Search by merchant name (partial match)
            amount: Exact amount to search for
            amount_range: Tuple of (min, max) amount

        Returns:
            Matching transactions
        """
        try:
            results = self.transactions.copy()

            if merchant_name:
                results = [
                    t for t in results
                    if merchant_name.lower() in t["merchant_name"].lower()
                ]

            if amount:
                results = [
                    t for t in results
                    if abs(t["amount"] - amount) < 0.01
                ]

            if amount_range:
                min_amount, max_amount = amount_range
                results = [
                    t for t in results
                    if min_amount <= t["amount"] <= max_amount
                ]

            logger.info(f"Found {len(results)} matching transactions")

            return {
                "success": True,
                "transactions": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return {"success": False, "error": str(e), "transactions": []}

    async def file_dispute(
        self,
        transaction_id: str,
        reason: str,
        description: str,
        supporting_docs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        File a dispute for a transaction.

        Args:
            transaction_id: Transaction to dispute
            reason: Reason for dispute
            description: Detailed description
            supporting_docs: List of supporting document references

        Returns:
            Dispute confirmation
        """
        try:
            # Find the transaction
            transaction = next(
                (t for t in self.transactions if t["transaction_id"] == transaction_id),
                None
            )

            if not transaction:
                return {"success": False, "error": "Transaction not found"}

            # Create dispute record
            dispute = {
                "dispute_id": f"DSP-{datetime.now().year}{random.randint(100000, 999999)}",
                "transaction_id": transaction_id,
                "transaction_amount": transaction["amount"],
                "merchant_name": transaction["merchant_name"],
                "reason": reason,
                "description": description,
                "status": "submitted",
                "filed_date": datetime.now().isoformat(),
                "expected_resolution_date": (datetime.now() + timedelta(days=45)).date().isoformat(),
                "case_number": f"CASE-{random.randint(10000, 99999)}",
                "provisional_credit": transaction["amount"] if transaction["amount"] > 100 else 0,
                "provisional_credit_date": (datetime.now() + timedelta(days=10)).date().isoformat() if transaction["amount"] > 100 else None,
                "supporting_docs": supporting_docs or []
            }

            self.disputes.append(dispute)

            logger.info(f"Filed dispute {dispute['dispute_id']} for transaction {transaction_id}")

            return {
                "success": True,
                "message": "Dispute filed successfully",
                "dispute": dispute,
                "next_steps": [
                    "Your dispute has been submitted for review",
                    f"Case number: {dispute['case_number']}",
                    f"Expected resolution: {dispute['expected_resolution_date']}",
                    "You will receive email updates on the status",
                    "Check dispute status anytime in your account"
                ]
            }
        except Exception as e:
            logger.error(f"Error filing dispute: {e}")
            return {"success": False, "error": str(e)}

    async def get_dispute_status(self, dispute_id: str) -> Dict[str, Any]:
        """
        Get status of a dispute.

        Args:
            dispute_id: Dispute identifier

        Returns:
            Dispute status
        """
        try:
            dispute = next(
                (d for d in self.disputes if d["dispute_id"] == dispute_id),
                None
            )

            if not dispute:
                return {"success": False, "error": "Dispute not found"}

            return {
                "success": True,
                "dispute": dispute
            }
        except Exception as e:
            logger.error(f"Error retrieving dispute: {e}")
            return {"success": False, "error": str(e)}

    async def download_statement(
        self,
        statement_date: Optional[str] = None,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Generate/download a statement.

        Args:
            statement_date: Statement date (defaults to most recent)
            format: Format (pdf, csv, excel)

        Returns:
            Statement download information
        """
        try:
            # Mock statement generation
            if not statement_date:
                statement_date = datetime.now().replace(day=1).date().isoformat()

            statement = {
                "statement_id": f"STMT-{datetime.now().year}{random.randint(1000, 9999)}",
                "statement_date": statement_date,
                "format": format,
                "download_url": f"/api/statements/download/{statement_date}.{format}",
                "generated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
            }

            logger.info(f"Generated statement for {statement_date}")

            return {
                "success": True,
                "statement": statement,
                "message": f"Statement ready for download in {format.upper()} format"
            }
        except Exception as e:
            logger.error(f"Error generating statement: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_transaction_service_instance = None


def get_transaction_service() -> MockTransactionService:
    """Get singleton instance of MockTransactionService"""
    global _transaction_service_instance
    if _transaction_service_instance is None:
        _transaction_service_instance = MockTransactionService()
    return _transaction_service_instance
