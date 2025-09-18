from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RiskFactor:
    name: str
    weight: Decimal
    value: Decimal
    description: str

class RiskScoringService:
    """
    Advanced risk scoring service that calculates comprehensive risk scores
    based on multiple factors including transaction patterns, user behavior,
    and external risk indicators.
    """
    
    def __init__(self):
        self.base_weights = {
            'amount_anomaly': Decimal('0.25'),
            'velocity_check': Decimal('0.20'),
            'location_risk': Decimal('0.15'),
            'time_anomaly': Decimal('0.10'),
            'merchant_risk': Decimal('0.15'),
            'card_usage_pattern': Decimal('0.15')
        }
        
        # Transaction history for velocity checks (in production, use database)
        self.transaction_history = {}
        
    def calculate_comprehensive_risk_score(self, transaction_data: Dict, 
                                         user_history: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate a comprehensive risk score based on multiple factors.
        
        Args:
            transaction_data: Current transaction details
            user_history: Historical transactions for the user
            
        Returns:
            Dict containing risk score, factors, and recommendations
        """
        risk_factors = []
        total_score = Decimal('0.0')
        
        # Amount anomaly detection
        amount_factor = self._analyze_amount_anomaly(transaction_data, user_history)
        if amount_factor:
            risk_factors.append(amount_factor)
            total_score += amount_factor.weight * amount_factor.value
            
        # Velocity checks
        velocity_factor = self._analyze_transaction_velocity(transaction_data)
        if velocity_factor:
            risk_factors.append(velocity_factor)
            total_score += velocity_factor.weight * velocity_factor.value
            
        # Location risk assessment
        location_factor = self._analyze_location_risk(transaction_data)
        if location_factor:
            risk_factors.append(location_factor)
            total_score += location_factor.weight * location_factor.value
            
        # Time-based anomaly detection
        time_factor = self._analyze_time_anomaly(transaction_data, user_history)
        if time_factor:
            risk_factors.append(time_factor)
            total_score += time_factor.weight * time_factor.value
            
        # Merchant risk assessment
        merchant_factor = self._analyze_merchant_risk(transaction_data)
        if merchant_factor:
            risk_factors.append(merchant_factor)
            total_score += merchant_factor.weight * merchant_factor.value
            
        # Card usage pattern analysis
        pattern_factor = self._analyze_usage_pattern(transaction_data, user_history)
        if pattern_factor:
            risk_factors.append(pattern_factor)
            total_score += pattern_factor.weight * pattern_factor.value
        
        return {
            'risk_score': float(min(total_score, Decimal('1.0'))),  # Cap at 1.0
            'risk_level': self._get_risk_level(total_score),
            'factors': [self._factor_to_dict(f) for f in risk_factors],
            'recommendations': self._generate_recommendations(total_score, risk_factors),
            'confidence': self._calculate_confidence(risk_factors)
        }
    
    def _analyze_amount_anomaly(self, transaction_data: Dict, 
                               user_history: Optional[List[Dict]]) -> Optional[RiskFactor]:
        """Detect if transaction amount is anomalous for this user."""
        current_amount = Decimal(str(transaction_data.get('amount', 0)))
        
        if not user_history:
            # No history - flag high amounts with graduated scoring
            if current_amount > Decimal('5000'):
                return RiskFactor(
                    name='amount_anomaly',
                    weight=self.base_weights['amount_anomaly'],
                    value=Decimal('0.9'),
                    description=f'Very high amount ${current_amount} with no transaction history'
                )
            elif current_amount > Decimal('2000'):
                return RiskFactor(
                    name='amount_anomaly',
                    weight=self.base_weights['amount_anomaly'],
                    value=Decimal('0.6'),
                    description=f'High amount ${current_amount} with no transaction history'
                )
            return None
            
        # Calculate user's typical spending patterns
        amounts = [Decimal(str(t.get('amount', 0))) for t in user_history[-30:]]  # Last 30 transactions
        if not amounts:
            return None
            
        avg_amount = sum(amounts) / len(amounts)
        max_amount = max(amounts)
        
        # Check if current amount is significantly higher than usual
        if current_amount > avg_amount * 3 and current_amount > max_amount * 1.5:
            anomaly_score = min(Decimal('1.0'), current_amount / (avg_amount * 5))
            return RiskFactor(
                name='amount_anomaly',
                weight=self.base_weights['amount_anomaly'],
                value=anomaly_score,
                description=f'Amount ${current_amount} is {float(current_amount/avg_amount):.1f}x higher than average'
            )
        
        return None
    
    def _analyze_transaction_velocity(self, transaction_data: Dict) -> Optional[RiskFactor]:
        """Check for rapid successive transactions (velocity fraud)."""
        card_number = transaction_data.get('card_number', '')
        timestamp = transaction_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            current_time = datetime.fromisoformat(timestamp)
        else:
            current_time = timestamp
        
        # Get recent transactions for this card
        if card_number not in self.transaction_history:
            self.transaction_history[card_number] = []
            
        recent_transactions = self.transaction_history[card_number]
        
        # Count transactions in last 5 minutes
        five_min_ago = current_time - timedelta(minutes=5)
        recent_count = sum(1 for t in recent_transactions if t > five_min_ago)
        
        # Add current transaction
        self.transaction_history[card_number].append(current_time)
        
        # Clean old transactions (keep last 24 hours)
        day_ago = current_time - timedelta(hours=24)
        self.transaction_history[card_number] = [
            t for t in self.transaction_history[card_number] if t > day_ago
        ]
        
        if recent_count >= 3:  # 3+ transactions in 5 minutes
            velocity_score = min(Decimal('1.0'), Decimal(str(recent_count)) / Decimal('5'))
            return RiskFactor(
                name='velocity_check',
                weight=self.base_weights['velocity_check'],
                value=velocity_score,
                description=f'{recent_count} transactions in last 5 minutes'
            )
        
        return None
    
    def _analyze_location_risk(self, transaction_data: Dict) -> Optional[RiskFactor]:
        """Assess risk based on transaction location."""
        location = transaction_data.get('location', '').upper()
        
        # High-risk countries/regions
        high_risk_indicators = ['UNKNOWN', 'OFFSHORE', 'SANCTIONED']
        high_risk_countries = ['RU', 'CN', 'IR', 'KP', 'SY', 'RUSSIA', 'CHINA', 'IRAN', 'MOSCOW', 'BEIJING']
        
        risk_score = Decimal('0.0')
        description = ""
        
        for indicator in high_risk_indicators:
            if indicator in location:
                risk_score = Decimal('0.9')
                description = f"Transaction from high-risk location: {location}"
                break
                
        for country in high_risk_countries:
            if country in location:
                risk_score = max(risk_score, Decimal('0.7'))
                description = f"Transaction from monitored country: {location}"
                break
        
        if risk_score > 0:
            return RiskFactor(
                name='location_risk',
                weight=self.base_weights['location_risk'],
                value=risk_score,
                description=description
            )
        
        return None
    
    def _analyze_time_anomaly(self, transaction_data: Dict, 
                             user_history: Optional[List[Dict]]) -> Optional[RiskFactor]:
        """Detect unusual transaction times for the user."""
        timestamp = transaction_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            current_time = datetime.fromisoformat(timestamp)
        else:
            current_time = timestamp
        hour = current_time.hour
        
        # Flag transactions between 2 AM and 5 AM as potentially suspicious
        if 2 <= hour <= 5:
            return RiskFactor(
                name='time_anomaly',
                weight=self.base_weights['time_anomaly'],
                value=Decimal('0.6'),
                description=f"Transaction at unusual hour: {hour:02d}:00"
            )
        
        return None
    
    def _analyze_merchant_risk(self, transaction_data: Dict) -> Optional[RiskFactor]:
        """Assess merchant-based risk factors."""
        merchant = transaction_data.get('merchant', '').upper()
        
        # High-risk merchant categories
        high_risk_merchants = ['CASINO', 'GAMBLING', 'CRYPTO', 'ADULT', 'UNKNOWN MERCHANT', 'CASH ADVANCE', 'ATM CASH', 'WIRE TRANSFER']
        
        for risk_merchant in high_risk_merchants:
            if risk_merchant in merchant:
                return RiskFactor(
                    name='merchant_risk',
                    weight=self.base_weights['merchant_risk'],
                    value=Decimal('0.7'),
                    description=f"High-risk merchant category: {merchant}"
                )
        
        return None
    
    def _analyze_usage_pattern(self, transaction_data: Dict, 
                              user_history: Optional[List[Dict]]) -> Optional[RiskFactor]:
        """Analyze if transaction fits user's typical usage patterns."""
        if not user_history or len(user_history) < 5:
            return None
            
        # Analyze typical merchant categories
        current_merchant = transaction_data.get('merchant', '').upper()
        historical_merchants = [t.get('merchant', '').upper() for t in user_history[-20:]]
        
        # If user has never used this type of merchant before
        merchant_words = set(current_merchant.split())
        historical_words = set()
        for merchant in historical_merchants:
            historical_words.update(merchant.split())
        
        if merchant_words.isdisjoint(historical_words) and len(historical_merchants) > 10:
            return RiskFactor(
                name='card_usage_pattern',
                weight=self.base_weights['card_usage_pattern'],
                value=Decimal('0.5'),
                description=f"First transaction with merchant type: {current_merchant}"
            )
        
        return None
    
    def _get_risk_level(self, score: Decimal) -> str:
        """Convert risk score to risk level."""
        if score >= Decimal('0.8'):
            return 'CRITICAL'
        elif score >= Decimal('0.6'):
            return 'HIGH'
        elif score >= Decimal('0.4'):
            return 'MEDIUM'
        elif score >= Decimal('0.2'):
            return 'LOW'
        return 'MINIMAL'
    
    def _generate_recommendations(self, score: Decimal, factors: List[RiskFactor]) -> List[str]:
        """Generate actionable recommendations based on risk factors."""
        recommendations = []
        
        if score >= Decimal('0.8'):
            recommendations.append("BLOCK transaction immediately")
            recommendations.append("Contact cardholder for verification")
            recommendations.append("Flag account for manual review")
        elif score >= Decimal('0.6'):
            recommendations.append("Require additional authentication")
            recommendations.append("Monitor account closely")
        elif score >= Decimal('0.4'):
            recommendations.append("Send SMS verification to cardholder")
            recommendations.append("Log for pattern analysis")
        
        # Factor-specific recommendations
        factor_names = [f.name for f in factors]
        if 'velocity_check' in factor_names:
            recommendations.append("Implement temporary transaction limits")
        if 'location_risk' in factor_names:
            recommendations.append("Verify location with cardholder")
        if 'amount_anomaly' in factor_names:
            recommendations.append("Confirm large purchase authorization")
            
        return recommendations
    
    def _calculate_confidence(self, factors: List[RiskFactor]) -> float:
        """Calculate confidence level in the risk assessment."""
        if not factors:
            return 0.3  # Low confidence with no factors
            
        # Higher confidence with more factors and higher weights
        total_weight = sum(f.weight for f in factors)
        factor_count_bonus = min(Decimal('0.2'), Decimal(str(len(factors))) * Decimal('0.05'))
        
        confidence = min(Decimal('1.0'), total_weight + factor_count_bonus)
        return float(confidence)
    
    def _factor_to_dict(self, factor: RiskFactor) -> Dict:
        """Convert RiskFactor to dictionary for JSON serialization."""
        return {
            'name': factor.name,
            'weight': float(factor.weight),
            'value': float(factor.value),
            'description': factor.description
        }
