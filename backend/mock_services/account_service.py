"""
Mock Account Service

Simulates account data API for demonstration purposes.
In production, this would integrate with real banking APIs.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class MockAccountService:
    """Mock service for account data and management"""

    def __init__(self):
        """Initialize mock account data"""
        self.accounts = {
            "demo_account_1": {
                "account_id": "ACC-BMO-2024-001",
                "cardholder_name": "Demo User",
                "card_type": "BMO Corporate World Elite Mastercard",
                "card_number_last4": "8247",
                "credit_limit": 25000.00,
                "current_balance": 4850.75,
                "available_credit": 20149.25,
                "statement_date": "2024-01-31",
                "payment_due_date": "2024-02-15",
                "minimum_payment": 145.00,
                "rewards_points": 24580,
                "rewards_value": 245.80,
                "account_status": "active",
                "card_status": "active",
                "authorized_users": 2,
                "spending_limit_per_transaction": 5000.00,
                "daily_spending_limit": 10000.00,
                "international_enabled": True,
                "contactless_enabled": True,
                "enrolled_programs": ["travel_insurance", "purchase_protection", "extended_warranty"]
            }
        }

    async def get_account_info(
        self,
        account_id: Optional[str] = None,
        card_last4: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get account information.

        Args:
            account_id: Account identifier
            card_last4: Last 4 digits of card

        Returns:
            Account data dictionary
        """
        try:
            # For demo, return default account
            account = self.accounts["demo_account_1"]

            logger.info(f"Retrieved account info for {account.get('account_id')}")

            return {
                "success": True,
                "account": account
            }
        except Exception as e:
            logger.error(f"Error retrieving account: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_balance_summary(self, account_id: str = "demo_account_1") -> Dict[str, Any]:
        """
        Get account balance summary.

        Args:
            account_id: Account identifier

        Returns:
            Balance summary
        """
        try:
            account = self.accounts.get(account_id)
            if not account:
                return {"success": False, "error": "Account not found"}

            return {
                "success": True,
                "balance_summary": {
                    "credit_limit": account["credit_limit"],
                    "current_balance": account["current_balance"],
                    "available_credit": account["available_credit"],
                    "pending_transactions": 325.50,  # Mock pending amount
                    "available_after_pending": account["available_credit"] - 325.50
                }
            }
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {"success": False, "error": str(e)}

    async def get_rewards_info(self, account_id: str = "demo_account_1") -> Dict[str, Any]:
        """
        Get rewards program information.

        Args:
            account_id: Account identifier

        Returns:
            Rewards data
        """
        try:
            account = self.accounts.get(account_id)
            if not account:
                return {"success": False, "error": "Account not found"}

            return {
                "success": True,
                "rewards": {
                    "points_balance": account["rewards_points"],
                    "points_value": account["rewards_value"],
                    "points_expiring": {
                        "amount": 1250,
                        "expiry_date": "2025-06-30"
                    },
                    "earning_rate": {
                        "travel": "3 points per $1",
                        "dining": "2 points per $1",
                        "other": "1 point per $1"
                    },
                    "redemption_options": [
                        "travel",
                        "cash_back",
                        "merchandise",
                        "statement_credit"
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error getting rewards: {e}")
            return {"success": False, "error": str(e)}

    async def update_spending_limit(
        self,
        account_id: str,
        limit_type: str,  # "transaction" or "daily"
        new_limit: float
    ) -> Dict[str, Any]:
        """
        Update spending limits.

        Args:
            account_id: Account identifier
            limit_type: Type of limit to update
            new_limit: New limit amount

        Returns:
            Update confirmation
        """
        try:
            account = self.accounts.get(account_id, self.accounts["demo_account_1"])

            if limit_type == "transaction":
                old_limit = account["spending_limit_per_transaction"]
                account["spending_limit_per_transaction"] = new_limit
            elif limit_type == "daily":
                old_limit = account["daily_spending_limit"]
                account["daily_spending_limit"] = new_limit
            else:
                return {"success": False, "error": "Invalid limit type"}

            logger.info(f"Updated {limit_type} limit from {old_limit} to {new_limit}")

            return {
                "success": True,
                "message": f"Successfully updated {limit_type} limit",
                "old_limit": old_limit,
                "new_limit": new_limit
            }
        except Exception as e:
            logger.error(f"Error updating limit: {e}")
            return {"success": False, "error": str(e)}

    async def add_authorized_user(
        self,
        account_id: str,
        user_name: str,
        spending_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Add an authorized user to the account.

        Args:
            account_id: Account identifier
            user_name: Name of authorized user
            spending_limit: Optional spending limit for this user

        Returns:
            Confirmation with new user details
        """
        try:
            account = self.accounts.get(account_id, self.accounts["demo_account_1"])

            new_user = {
                "name": user_name,
                "card_last4": str(random.randint(1000, 9999)),
                "status": "pending_activation",
                "spending_limit": spending_limit or 2500.00,
                "added_date": datetime.now().isoformat()
            }

            account["authorized_users"] += 1

            logger.info(f"Added authorized user: {user_name}")

            return {
                "success": True,
                "message": f"Successfully added {user_name} as authorized user",
                "user_details": new_user,
                "card_delivery_eta": "7-10 business days"
            }
        except Exception as e:
            logger.error(f"Error adding authorized user: {e}")
            return {"success": False, "error": str(e)}

    async def check_card_status(
        self,
        card_last4: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check card status (active, blocked, lost, etc.).

        Args:
            card_last4: Last 4 digits of card

        Returns:
            Card status information
        """
        try:
            account = self.accounts["demo_account_1"]

            return {
                "success": True,
                "card_status": {
                    "status": account["card_status"],
                    "card_last4": account["card_number_last4"],
                    "activation_date": "2023-06-15",
                    "expiry_date": "2027-05",
                    "cvv_last_verified": "2025-01-15",
                    "blocked": False,
                    "reported_lost": False,
                    "replacement_ordered": False
                }
            }
        except Exception as e:
            logger.error(f"Error checking card status: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_account_service_instance = None


def get_account_service() -> MockAccountService:
    """Get singleton instance of MockAccountService"""
    global _account_service_instance
    if _account_service_instance is None:
        _account_service_instance = MockAccountService()
    return _account_service_instance
