"""
Mock Services Package

Provides mock/simulated backend services for demonstration.
"""

from .account_service import get_account_service, MockAccountService
from .transaction_service import get_transaction_service, MockTransactionService
from .analytics_service import get_analytics_service, MockAnalyticsService

__all__ = [
    "get_account_service",
    "get_transaction_service",
    "get_analytics_service",
    "MockAccountService",
    "MockTransactionService",
    "MockAnalyticsService"
]
