from decimal import Decimal
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Transaction:
    id: str
    amount: Decimal
    merchant: str
    location: str
    timestamp: datetime
    card_number: str  # Masked
    
class FraudDetectionService:
    """
    Core fraud detection service for FinTechCo.
    Currently implements basic rule-based detection.
    TODO: Integrate ML model for advanced detection
    """
    
    def __init__(self):
        self.risk_threshold = Decimal('0.7')
        self.high_risk_countries = ['RU', 'CN', 'IR', 'KP', 'SY', 'RUSSIA', 'CHINA', 'IRAN']
        self.high_risk_merchants = ['CASH ADVANCE', 'CASINO', 'GAMBLING', 'CRYPTO', 'ADULT', 'UNKNOWN MERCHANT']
        
    def analyze_transaction(self, transaction: Transaction) -> Dict:
        """
        Analyze a transaction for fraud indicators.
        Returns risk score and factors.
        """
        risk_score = Decimal('0.0')
        risk_factors = []
        
        # Check amount threshold - lowered for better detection
        if transaction.amount > Decimal('5000'):
            risk_score += Decimal('0.4')
            risk_factors.append('high_amount')
        elif transaction.amount > Decimal('2000'):
            risk_score += Decimal('0.2')
            risk_factors.append('elevated_amount')
            
        # Check location
        if self._is_high_risk_location(transaction.location):
            risk_score += Decimal('0.4')
            risk_factors.append('risky_location')

        # Check merchant type
        if self._is_high_risk_merchant(transaction.merchant):
            risk_score += Decimal('0.3')
            risk_factors.append('risky_merchant')

        # TODO: Add velocity checks
        # TODO: Add ML model scoring
        
        return {
            'transaction_id': transaction.id,
            'risk_score': float(risk_score),  # Convert for JSON
            'risk_level': self._get_risk_level(risk_score),
            'factors': risk_factors,
            'timestamp': transaction.timestamp.isoformat()
        }
        
    def _get_risk_level(self, score: Decimal) -> str:
        if score >= Decimal('0.7'):
            return 'HIGH'
        elif score >= Decimal('0.4'):
            return 'MEDIUM'
        return 'LOW'
        
    def _is_high_risk_location(self, location: str) -> bool:
        # Check for high-risk countries and regions
        location_upper = location.upper()
        return any(country in location_upper for country in self.high_risk_countries)

    def _is_high_risk_merchant(self, merchant: str) -> bool:
        # Check for high-risk merchant types
        merchant_upper = merchant.upper()
        return any(risk_merchant in merchant_upper for risk_merchant in self.high_risk_merchants)