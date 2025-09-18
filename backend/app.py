from flask import Flask, request, jsonify
from flask_cors import CORS
from decimal import Decimal
from datetime import datetime
import logging
import os
from typing import Dict, List

# Import our services
from services.fraud_detection import FraudDetectionService, Transaction
from services.risk_scoring import RiskScoringService
from services.transaction_validator import TransactionValidator
from models.ml_model import FraudDetectionMLModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize services
fraud_service = FraudDetectionService()
risk_service = RiskScoringService()
validator = TransactionValidator()
ml_model = FraudDetectionMLModel()

# In-memory storage for demo (use database in production)
transactions_db = []
alerts_db = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'fraud_detection': 'active',
            'risk_scoring': 'active',
            'transaction_validator': 'active',
            'ml_model': 'trained' if ml_model.is_trained else 'not_trained'
        }
    })

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with risk scores."""
    try:
        # Add pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        risk_level = request.args.get('risk_level')  # Filter by risk level
        
        filtered_transactions = transactions_db
        
        # Filter by risk level if specified
        if risk_level:
            filtered_transactions = [
                t for t in transactions_db 
                if t.get('risk_analysis', {}).get('risk_level', '').upper() == risk_level.upper()
            ]
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_transactions = filtered_transactions[start_idx:end_idx]
        
        return jsonify({
            'transactions': paginated_transactions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(filtered_transactions),
                'pages': (len(filtered_transactions) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        return jsonify({'error': 'Failed to retrieve transactions'}), 500

@app.route('/api/transactions', methods=['POST'])
def analyze_transaction():
    """Analyze a new transaction for fraud."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No transaction data provided'}), 400
        
        # Validate transaction data
        logger.info(f"Validating transaction data: {data}")
        validation_result = validator.validate_transaction(data)
        
        if not validation_result.is_valid:
            logger.error(f"Validation failed: {validation_result.errors}")
            return jsonify({
                'error': 'Transaction validation failed',
                'validation_errors': validation_result.errors,
                'validation_warnings': validation_result.warnings
            }), 400
        
        # Use sanitized data
        clean_data = validation_result.sanitized_data
        logger.info(f"Clean data after validation: {clean_data}")
        
        # Create Transaction object for fraud detection
        transaction = Transaction(
            id=clean_data['id'],
            amount=clean_data['amount'],
            merchant=clean_data['merchant'],
            location=clean_data['location'],
            timestamp=clean_data['timestamp'],
            card_number=clean_data['card_number']
        )
        
        # Basic fraud detection
        fraud_analysis = fraud_service.analyze_transaction(transaction)
        
        # Advanced risk scoring
        risk_analysis = risk_service.calculate_comprehensive_risk_score(
            clean_data,
            user_history=get_user_transaction_history(clean_data['card_number'])
        )
        
        # ML model prediction (if trained)
        ml_prediction = None
        if ml_model.is_trained:
            try:
                ml_results = ml_model.predict_fraud_probability([clean_data])
                ml_prediction = ml_results[0] if ml_results else None
            except Exception as e:
                logger.warning(f"ML prediction failed: {str(e)}")
        
        # Combine all analyses
        combined_result = {
            'transaction_id': clean_data['id'],
            'timestamp': clean_data['timestamp'].isoformat() if hasattr(clean_data['timestamp'], 'isoformat') else str(clean_data['timestamp']),
            'amount': float(clean_data['amount']),
            'merchant': clean_data['merchant'],
            'location': clean_data['location'],
            'card_number': clean_data['card_number'],
            'validation_warnings': validation_result.warnings,
            'fraud_analysis': fraud_analysis,
            'risk_analysis': risk_analysis,
            'ml_prediction': ml_prediction,
            'final_decision': determine_final_decision(fraud_analysis, risk_analysis, ml_prediction)
        }
        
        # Store transaction
        transactions_db.append(combined_result)
        
        # Create alert if high risk
        if combined_result['final_decision']['action'] in ['BLOCK', 'REVIEW']:
            create_alert(combined_result)
        
        return jsonify(combined_result)
        
    except Exception as e:
        logger.error(f"Error analyzing transaction: {str(e)}")
        return jsonify({'error': 'Transaction analysis failed'}), 500

@app.route('/api/transactions/batch', methods=['POST'])
def analyze_batch_transactions():
    """Analyze multiple transactions in batch."""
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({'error': 'No transactions provided'}), 400
        
        transactions = data['transactions']
        results = []
        
        # Validate all transactions first
        validation_results = validator.validate_batch_transactions(transactions)
        
        for i, (transaction_data, validation_result) in enumerate(zip(transactions, validation_results)):
            if not validation_result.is_valid:
                results.append({
                    'transaction_index': i,
                    'error': 'Validation failed',
                    'validation_errors': validation_result.errors
                })
                continue
            
            # Process valid transaction (simplified for batch)
            clean_data = validation_result.sanitized_data
            
            transaction = Transaction(
                id=clean_data['id'],
                amount=clean_data['amount'],
                merchant=clean_data['merchant'],
                location=clean_data['location'],
                timestamp=clean_data['timestamp'],
                card_number=clean_data['card_number']
            )
            
            fraud_analysis = fraud_service.analyze_transaction(transaction)
            
            result = {
                'transaction_index': i,
                'transaction_id': clean_data['id'],
                'fraud_analysis': fraud_analysis,
                'validation_warnings': validation_result.warnings
            }
            
            results.append(result)
            transactions_db.append(result)
        
        # Generate batch summary
        validation_summary = validator.get_validation_summary(validation_results)
        
        return jsonify({
            'results': results,
            'summary': {
                'total_processed': len(transactions),
                'successful': len([r for r in results if 'error' not in r]),
                'failed': len([r for r in results if 'error' in r]),
                'validation_summary': validation_summary
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return jsonify({'error': 'Batch analysis failed'}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get fraud alerts."""
    try:
        severity = request.args.get('severity')  # Filter by severity
        limit = int(request.args.get('limit', 100))
        
        filtered_alerts = alerts_db
        
        if severity:
            filtered_alerts = [
                alert for alert in alerts_db 
                if alert.get('severity', '').upper() == severity.upper()
            ]
        
        # Sort by timestamp (most recent first) and limit
        sorted_alerts = sorted(
            filtered_alerts, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )[:limit]
        
        return jsonify({
            'alerts': sorted_alerts,
            'total_count': len(filtered_alerts)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}")
        return jsonify({'error': 'Failed to retrieve alerts'}), 500

@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Get ML model information."""
    try:
        return jsonify(ml_model.get_model_info())
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({'error': 'Failed to get model info'}), 500

@app.route('/api/model/train', methods=['POST'])
def train_model():
    """Train the ML model with provided data or synthetic data."""
    try:
        data = request.get_json()
        
        if data and 'transactions' in data and 'labels' in data:
            # Use provided training data
            transactions = data['transactions']
            labels = data['labels']
        else:
            # Generate synthetic training data for demo
            logger.info("Generating synthetic training data...")
            transactions, labels = ml_model.generate_synthetic_training_data(1000)
        
        # Train the model
        training_results = ml_model.train_models(transactions, labels)
        
        return jsonify({
            'status': 'success',
            'message': 'Model training completed',
            'training_results': training_results
        })
        
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return jsonify({'error': 'Model training failed'}), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get fraud detection statistics."""
    try:
        total_transactions = len(transactions_db)
        
        if total_transactions == 0:
            return jsonify({
                'total_transactions': 0,
                'fraud_rate': 0,
                'risk_distribution': {},
                'alerts_count': len(alerts_db)
            })
        
        # Calculate risk level distribution
        risk_levels = {}
        fraud_count = 0
        
        for transaction in transactions_db:
            risk_level = transaction.get('risk_analysis', {}).get('risk_level', 'UNKNOWN')
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            # Count high-risk transactions as potential fraud
            if risk_level in ['HIGH', 'CRITICAL']:
                fraud_count += 1
        
        fraud_rate = (fraud_count / total_transactions) * 100 if total_transactions > 0 else 0
        
        return jsonify({
            'total_transactions': total_transactions,
            'fraud_rate': round(fraud_rate, 2),
            'risk_distribution': risk_levels,
            'alerts_count': len(alerts_db),
            'model_status': 'trained' if ml_model.is_trained else 'not_trained'
        })
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500

def get_user_transaction_history(card_number: str, limit: int = 30) -> List[Dict]:
    """Get transaction history for a specific card."""
    user_transactions = [
        t for t in transactions_db 
        if t.get('card_number') == card_number
    ]
    
    # Sort by timestamp and return recent transactions
    sorted_transactions = sorted(
        user_transactions,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    return sorted_transactions[:limit]

def determine_final_decision(fraud_analysis: Dict, risk_analysis: Dict, ml_prediction: Dict = None) -> Dict:
    """Determine final action based on all analyses."""
    # Get risk scores
    basic_risk = fraud_analysis.get('risk_score', 0)
    advanced_risk = risk_analysis.get('risk_score', 0)
    ml_risk = ml_prediction.get('combined_fraud_probability', 0) if ml_prediction else 0
    
    # Weighted combination
    if ml_prediction:
        final_score = 0.4 * basic_risk + 0.3 * advanced_risk + 0.3 * ml_risk
    else:
        final_score = 0.6 * basic_risk + 0.4 * advanced_risk
    
    # Determine action
    if final_score >= 0.8:
        action = 'BLOCK'
        reason = 'Critical fraud risk detected'
    elif final_score >= 0.6:
        action = 'REVIEW'
        reason = 'High fraud risk - manual review required'
    elif final_score >= 0.4:
        action = 'MONITOR'
        reason = 'Medium fraud risk - enhanced monitoring'
    else:
        action = 'APPROVE'
        reason = 'Low fraud risk'
    
    return {
        'final_risk_score': round(final_score, 3),
        'action': action,
        'reason': reason,
        'confidence': risk_analysis.get('confidence', 0.5)
    }

def create_alert(transaction_result: Dict):
    """Create a fraud alert for high-risk transactions."""
    decision = transaction_result.get('final_decision', {})
    
    if decision.get('action') in ['BLOCK', 'REVIEW']:
        severity = 'CRITICAL' if decision.get('action') == 'BLOCK' else 'HIGH'
        
        alert = {
            'id': f"ALERT_{len(alerts_db) + 1:06d}",
            'transaction_id': transaction_result.get('transaction_id'),
            'severity': severity,
            'risk_score': decision.get('final_risk_score', 0),
            'action_required': decision.get('action'),
            'reason': decision.get('reason'),
            'merchant': transaction_result.get('merchant'),
            'amount': transaction_result.get('amount'),
            'location': transaction_result.get('location'),
            'created_at': datetime.now().isoformat(),
            'status': 'OPEN'
        }
        
        alerts_db.append(alert)
        logger.warning(f"Fraud alert created: {alert['id']} for transaction {alert['transaction_id']}")

if __name__ == '__main__':
    # Initialize with some demo data
    logger.info("Starting Fraud Detection API...")
    
    # Train model with synthetic data if not already trained
    if not ml_model.is_trained:
        try:
            logger.info("Training ML model with synthetic data...")
            transactions, labels = ml_model.generate_synthetic_training_data(500)
            ml_model.train_models(transactions, labels)
            logger.info("ML model training completed")
        except Exception as e:
            logger.warning(f"Could not train ML model: {str(e)}")
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5001))  # Default to 5001 to match frontend proxy
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
