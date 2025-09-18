from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_data: Optional[Dict] = None

class TransactionValidator:
    """
    Comprehensive transaction validation service that ensures data integrity,
    security compliance, and business rule adherence for all financial transactions.
    """
    
    def __init__(self):
        self.max_transaction_amount = Decimal('50000.00')  # $50,000 daily limit
        self.min_transaction_amount = Decimal('0.01')      # $0.01 minimum
        self.blocked_merchants = {'BLOCKED_MERCHANT_1', 'BLOCKED_MERCHANT_2'}
        self.allowed_currencies = {'USD', 'EUR', 'GBP', 'CAD'}
        
    def validate_transaction(self, transaction_data: Dict) -> ValidationResult:
        """
        Perform comprehensive validation of transaction data.
        
        Args:
            transaction_data: Raw transaction data to validate
            
        Returns:
            ValidationResult with validation status and sanitized data
        """
        errors = []
        warnings = []
        sanitized_data = {}
        
        try:
            # Required field validation
            required_fields = ['id', 'amount', 'merchant', 'location', 'timestamp', 'card_number']
            missing_fields = [field for field in required_fields if field not in transaction_data]
            
            if missing_fields:
                errors.extend([f"Missing required field: {field}" for field in missing_fields])
                return ValidationResult(False, errors, warnings)
            
            # Validate and sanitize each field
            sanitized_data['id'] = self._validate_transaction_id(transaction_data['id'], errors)
            sanitized_data['amount'] = self._validate_amount(transaction_data['amount'], errors, warnings)
            sanitized_data['merchant'] = self._validate_merchant(transaction_data['merchant'], errors, warnings)
            sanitized_data['location'] = self._validate_location(transaction_data['location'], errors)
            sanitized_data['timestamp'] = self._validate_timestamp(transaction_data['timestamp'], errors)
            sanitized_data['card_number'] = self._validate_card_number(transaction_data['card_number'], errors)
            
            # Optional fields
            if 'currency' in transaction_data:
                sanitized_data['currency'] = self._validate_currency(transaction_data['currency'], errors)
            else:
                sanitized_data['currency'] = 'USD'  # Default currency
                
            if 'description' in transaction_data:
                sanitized_data['description'] = self._sanitize_description(transaction_data['description'])
            
            # Business rule validation
            self._validate_business_rules(sanitized_data, errors, warnings)
            
            # Security validation
            self._validate_security_rules(sanitized_data, errors, warnings)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(is_valid, errors, warnings, sanitized_data if is_valid else None)
            
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}")
            errors.append(f"Validation system error: {str(e)}")
            return ValidationResult(False, errors, warnings)
    
    def _validate_transaction_id(self, transaction_id: str, errors: List[str]) -> Optional[str]:
        """Validate transaction ID format and uniqueness."""
        if not isinstance(transaction_id, str):
            errors.append("Transaction ID must be a string")
            return None
            
        # Remove whitespace
        transaction_id = transaction_id.strip()
        
        if not transaction_id:
            errors.append("Transaction ID cannot be empty")
            return None
            
        # Check format: alphanumeric, hyphens, underscores allowed
        if not re.match(r'^[A-Za-z0-9_-]+$', transaction_id):
            errors.append("Transaction ID contains invalid characters")
            return None
            
        if len(transaction_id) < 3 or len(transaction_id) > 50:
            errors.append("Transaction ID must be between 3 and 50 characters")
            return None
            
        return transaction_id
    
    def _validate_amount(self, amount, errors: List[str], warnings: List[str]) -> Optional[Decimal]:
        """Validate transaction amount with precision handling."""
        try:
            # Convert to Decimal for precision
            if isinstance(amount, str):
                # Remove currency symbols and whitespace
                amount_str = re.sub(r'[^\d.-]', '', amount.strip())
                decimal_amount = Decimal(amount_str)
            elif isinstance(amount, (int, float)):
                decimal_amount = Decimal(str(amount))
            else:
                errors.append(f"Invalid amount type: {type(amount)}")
                return None
                
            # Validate amount range
            if decimal_amount < self.min_transaction_amount:
                errors.append(f"Amount ${decimal_amount} is below minimum ${self.min_transaction_amount}")
                return None
                
            if decimal_amount > self.max_transaction_amount:
                errors.append(f"Amount ${decimal_amount} exceeds maximum ${self.max_transaction_amount}")
                return None
                
            # Check for reasonable decimal places (max 2 for currency)
            if decimal_amount.as_tuple().exponent < -2:
                warnings.append("Amount has more than 2 decimal places, rounding to cents")
                decimal_amount = decimal_amount.quantize(Decimal('0.01'))
                
            # Flag unusually large amounts
            if decimal_amount > Decimal('10000.00'):
                warnings.append(f"Large transaction amount: ${decimal_amount}")
                
            return decimal_amount
            
        except (InvalidOperation, ValueError) as e:
            errors.append(f"Invalid amount format: {str(e)}")
            return None
    
    def _validate_merchant(self, merchant: str, errors: List[str], warnings: List[str]) -> Optional[str]:
        """Validate and sanitize merchant information."""
        if not isinstance(merchant, str):
            errors.append("Merchant must be a string")
            return None
            
        # Sanitize merchant name
        merchant = merchant.strip()
        
        if not merchant:
            errors.append("Merchant name cannot be empty")
            return None
            
        if len(merchant) > 100:
            warnings.append("Merchant name truncated to 100 characters")
            merchant = merchant[:100]
            
        # Check against blocked merchants
        merchant_upper = merchant.upper()
        if any(blocked in merchant_upper for blocked in self.blocked_merchants):
            errors.append(f"Transactions with merchant '{merchant}' are not allowed")
            return None
            
        # Remove potentially harmful characters
        sanitized_merchant = re.sub(r'[<>"\']', '', merchant)
        if sanitized_merchant != merchant:
            warnings.append("Merchant name contained potentially harmful characters")
            
        return sanitized_merchant
    
    def _validate_location(self, location: str, errors: List[str]) -> Optional[str]:
        """Validate transaction location."""
        if not isinstance(location, str):
            errors.append("Location must be a string")
            return None
            
        location = location.strip()
        
        if not location:
            errors.append("Location cannot be empty")
            return None
            
        if len(location) > 200:
            errors.append("Location exceeds maximum length of 200 characters")
            return None
            
        # Basic format validation (City, Country or City, State, Country)
        if not re.match(r'^[A-Za-z\s,.-]+$', location):
            errors.append("Location contains invalid characters")
            return None
            
        return location
    
    def _validate_timestamp(self, timestamp, errors: List[str]) -> Optional[datetime]:
        """Validate transaction timestamp."""
        try:
            if isinstance(timestamp, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                errors.append(f"Invalid timestamp type: {type(timestamp)}")
                return None
            
            # Ensure both timestamps are timezone-aware for comparison
            now = datetime.now(timezone.utc)
            
            # Convert dt to UTC if it's naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if it has a different timezone
                dt = dt.astimezone(timezone.utc)
            
            # Check if timestamp is reasonable (not too far in past/future)
            # Allow 5 minutes in the future to account for clock skew
            future_threshold = now + timedelta(minutes=5)
            if dt > future_threshold:
                errors.append("Transaction timestamp cannot be in the future")
                return None
                
            # Allow transactions up to 30 days old
            thirty_days_ago = now - timedelta(days=30)
            if dt < thirty_days_ago:
                errors.append("Transaction timestamp is too old (>30 days)")
                return None
                
            return dt
            
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid timestamp format: {str(e)}")
            return None
    
    def _validate_card_number(self, card_number: str, errors: List[str]) -> Optional[str]:
        """Validate masked card number format."""
        if not isinstance(card_number, str):
            errors.append("Card number must be a string")
            return None
            
        card_number = card_number.strip()
        
        # Should be masked format like ****1234 or **** **** **** 1234
        masked_pattern = r'^\*{4,12}[\s\*]*\d{4}$'
        if not re.match(masked_pattern, card_number.replace(' ', '')):
            errors.append("Card number must be in masked format (e.g., ****1234)")
            return None
            
        # Ensure no full card numbers are exposed
        if re.search(r'\d{13,19}', card_number.replace(' ', '').replace('*', '')):
            errors.append("Full card numbers are not allowed for security")
            return None
            
        return card_number
    
    def _validate_currency(self, currency: str, errors: List[str]) -> Optional[str]:
        """Validate currency code."""
        if not isinstance(currency, str):
            errors.append("Currency must be a string")
            return None
            
        currency = currency.strip().upper()
        
        if currency not in self.allowed_currencies:
            errors.append(f"Currency '{currency}' is not supported. Allowed: {', '.join(self.allowed_currencies)}")
            return None
            
        return currency
    
    def _sanitize_description(self, description: str) -> str:
        """Sanitize optional transaction description."""
        if not isinstance(description, str):
            return ""
            
        # Remove potentially harmful content
        sanitized = re.sub(r'[<>"\']', '', description.strip())
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
            
        return sanitized
    
    def _validate_business_rules(self, data: Dict, errors: List[str], warnings: List[str]):
        """Apply business-specific validation rules."""
        # Rule: No transactions over $25,000 without pre-authorization
        if data.get('amount') and data['amount'] > Decimal('25000.00'):
            if not data.get('pre_authorized', False):
                warnings.append("Large transaction requires pre-authorization")
        
        # Rule: Weekend transactions over $10,000 require additional verification
        if data.get('timestamp') and data.get('amount'):
            if data['timestamp'].weekday() >= 5 and data['amount'] > Decimal('10000.00'):
                warnings.append("Weekend large transaction flagged for review")
        
        # Rule: International transactions require location verification
        location = data.get('location', '')
        if location and not any(country in location.upper() for country in ['US', 'USA', 'UNITED STATES']):
            warnings.append("International transaction requires location verification")
    
    def _validate_security_rules(self, data: Dict, errors: List[str], warnings: List[str]):
        """Apply security-specific validation rules."""
        # Check for suspicious patterns in merchant names
        merchant = data.get('merchant', '').upper()
        suspicious_keywords = ['TEST', 'TEMP', 'FAKE', 'DUMMY', 'SAMPLE']
        
        if any(keyword in merchant for keyword in suspicious_keywords):
            warnings.append(f"Merchant name contains suspicious keyword: {merchant}")
        
        # Validate transaction timing (flag rapid successive transactions)
        # This would typically check against a database of recent transactions
        timestamp = data.get('timestamp')
        if timestamp:
            # Placeholder for velocity checking logic
            # In production, this would query recent transactions for the card
            pass
    
    def validate_batch_transactions(self, transactions: List[Dict]) -> List[ValidationResult]:
        """Validate multiple transactions efficiently."""
        results = []
        
        for i, transaction in enumerate(transactions):
            try:
                result = self.validate_transaction(transaction)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating transaction {i}: {str(e)}")
                results.append(ValidationResult(
                    False, 
                    [f"Batch validation error: {str(e)}"], 
                    []
                ))
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict:
        """Generate summary statistics for batch validation results."""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        all_errors = []
        all_warnings = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return {
            'total_transactions': total,
            'valid_transactions': valid,
            'invalid_transactions': invalid,
            'validation_rate': round((valid / total * 100) if total > 0 else 0, 2),
            'common_errors': self._get_common_issues(all_errors),
            'common_warnings': self._get_common_issues(all_warnings)
        }
    
    def _get_common_issues(self, issues: List[str]) -> List[Dict]:
        """Identify most common validation issues."""
        from collections import Counter
        
        issue_counts = Counter(issues)
        return [
            {'issue': issue, 'count': count}
            for issue, count in issue_counts.most_common(5)
        ]
