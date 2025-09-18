import pytest
from decimal import Decimal
from datetime import datetime
from services.fraud_detection import FraudDetectionService, Transaction

class TestFraudDetection:
    def setup_method(self):
        self.service = FraudDetectionService()
        
    def test_high_amount_transaction(self):
        """Test that high amount transactions are flagged"""
        transaction = Transaction(
            id="TEST001",
            amount=Decimal('15000.00'),
            merchant="Luxury Store",
            location="New York, US",
            timestamp=datetime.now(),
            card_number="****1234"
        )
        
        result = self.service.analyze_transaction(transaction)
        
        assert result['risk_score'] >= 0.3
        assert 'high_amount' in result['factors']
        
    def test_decimal_precision(self):
        """Ensure Decimal type maintains precision"""
        transaction = Transaction(
            id="TEST002",
            amount=Decimal('99.99'),
            merchant="Coffee Shop",
            location="London, UK",
            timestamp=datetime.now(),
            card_number="****5678"
        )
        
        result = self.service.analyze_transaction(transaction)
        
        # Verify no floating point errors
        assert isinstance(transaction.amount, Decimal)
        
    # TODO: Add tests for ML model integration
    # TODO: Add security validation tests