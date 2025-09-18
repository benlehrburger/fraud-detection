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
        self.high_risk_countries = ['XX', 'YY', 'ZZ']
        
    def analyze_transaction(self, transaction: Transaction) -> Dict:
        """
        Analyze a transaction for fraud indicators.
        Returns risk score and factors.
        """
        risk_score = Decimal('0.0')
        risk_factors = []
        
        # Check amount threshold
        if transaction.amount > Decimal('10000'):
            risk_score += Decimal('0.3')
            risk_factors.append('high_amount')
            
        # Check location
        if self._is_high_risk_location(transaction.location):
            risk_score += Decimal('0.4')
            risk_factors.append('risky_location')
            
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
        # Simplified check - would be more complex in production
        return any(country in location for country in self.high_risk_countries)