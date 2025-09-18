import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class FraudDetectionMLModel:
    """
    Machine Learning model for fraud detection using ensemble methods.
    Combines anomaly detection (Isolation Forest) with supervised learning (Random Forest).
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.anomaly_model = None
        self.classification_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.model_path = model_path or 'models/'
        self.is_trained = False
        
        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)
        
        # Try to load existing models
        self._load_models()
    
    def prepare_features(self, transactions: List[Dict]) -> pd.DataFrame:
        """
        Convert transaction data into ML-ready features.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            DataFrame with engineered features
        """
        df = pd.DataFrame(transactions)
        
        # Convert timestamp to datetime if it's a string
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Extract time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        
        # Amount-based features
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df['log_amount'] = np.log1p(df['amount'])
            df['amount_rounded'] = (df['amount'] % 1 == 0).astype(int)  # Round number amounts
        
        # Location-based features
        if 'location' in df.columns:
            df['location_length'] = df['location'].str.len()
            df['is_international'] = (~df['location'].str.contains('US|USA|United States', case=False, na=False)).astype(int)
        
        # Merchant-based features
        if 'merchant' in df.columns:
            df['merchant_length'] = df['merchant'].str.len()
            df['merchant_words'] = df['merchant'].str.split().str.len()
            
            # Common merchant categories (simplified)
            df['is_online'] = df['merchant'].str.contains('ONLINE|WEB|INTERNET', case=False, na=False).astype(int)
            df['is_gas_station'] = df['merchant'].str.contains('GAS|FUEL|SHELL|EXXON', case=False, na=False).astype(int)
            df['is_restaurant'] = df['merchant'].str.contains('RESTAURANT|CAFE|FOOD', case=False, na=False).astype(int)
            df['is_retail'] = df['merchant'].str.contains('STORE|SHOP|RETAIL|WALMART|TARGET', case=False, na=False).astype(int)
        
        # Card-based features
        if 'card_number' in df.columns:
            # Extract last 4 digits for pattern analysis (already masked)
            df['card_last_4'] = df['card_number'].str.extract(r'(\d{4})$')
            df['card_last_4'] = pd.to_numeric(df['card_last_4'], errors='coerce')
        
        return df
    
    def engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features based on transaction patterns.
        
        Args:
            df: DataFrame with basic features
            
        Returns:
            DataFrame with additional engineered features
        """
        # Sort by timestamp for sequence-based features
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
        
        # Velocity features (transactions per time window)
        if 'card_number' in df.columns and 'timestamp' in df.columns:
            df['transactions_last_hour'] = df.groupby('card_number')['timestamp'].transform(
                lambda x: x.rolling('1H').count()
            )
            df['transactions_last_day'] = df.groupby('card_number')['timestamp'].transform(
                lambda x: x.rolling('1D').count()
            )
        
        # Amount pattern features
        if 'amount' in df.columns and 'card_number' in df.columns:
            # Rolling statistics
            df['amount_mean_7d'] = df.groupby('card_number')['amount'].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
            df['amount_std_7d'] = df.groupby('card_number')['amount'].transform(
                lambda x: x.rolling(window=7, min_periods=1).std()
            ).fillna(0)
            
            # Deviation from personal average
            df['amount_deviation'] = abs(df['amount'] - df['amount_mean_7d']) / (df['amount_std_7d'] + 1)
        
        # Merchant frequency features
        if 'merchant' in df.columns and 'card_number' in df.columns:
            merchant_counts = df.groupby(['card_number', 'merchant']).size().reset_index(name='merchant_frequency')
            df = df.merge(merchant_counts, on=['card_number', 'merchant'], how='left')
            df['is_new_merchant'] = (df['merchant_frequency'] == 1).astype(int)
        
        return df
    
    def train_models(self, transactions: List[Dict], labels: Optional[List[int]] = None) -> Dict:
        """
        Train both anomaly detection and classification models.
        
        Args:
            transactions: Training transaction data
            labels: Optional fraud labels (1 for fraud, 0 for legitimate)
            
        Returns:
            Training metrics and model information
        """
        logger.info("Starting model training...")
        
        # Prepare features
        df = self.prepare_features(transactions)
        df = self.engineer_advanced_features(df)
        
        # Select numerical features for ML
        numerical_features = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove target and ID columns
        exclude_cols = ['id', 'timestamp', 'card_number']
        self.feature_columns = [col for col in numerical_features if col not in exclude_cols]
        
        X = df[self.feature_columns].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train anomaly detection model (unsupervised)
        logger.info("Training anomaly detection model...")
        self.anomaly_model = IsolationForest(
            contamination=0.1,  # Assume 10% fraud rate
            random_state=42,
            n_estimators=100
        )
        self.anomaly_model.fit(X_scaled)
        
        training_results = {
            'feature_count': len(self.feature_columns),
            'training_samples': len(X),
            'features_used': self.feature_columns
        }
        
        # Train supervised model if labels are provided
        if labels is not None and len(labels) == len(X):
            logger.info("Training supervised classification model...")
            
            y = np.array(labels)
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            self.classification_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.classification_model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.classification_model.predict(X_test)
            
            training_results.update({
                'supervised_model_trained': True,
                'test_accuracy': self.classification_model.score(X_test, y_test),
                'classification_report': classification_report(y_test, y_pred, output_dict=True),
                'feature_importance': dict(zip(
                    self.feature_columns,
                    self.classification_model.feature_importances_
                ))
            })
        else:
            training_results['supervised_model_trained'] = False
        
        self.is_trained = True
        
        # Save models
        self._save_models()
        
        logger.info("Model training completed successfully")
        return training_results
    
    def predict_fraud_probability(self, transactions: List[Dict]) -> List[Dict]:
        """
        Predict fraud probability for new transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of prediction results with probabilities and explanations
        """
        if not self.is_trained:
            raise ValueError("Models must be trained before making predictions")
        
        # Prepare features
        df = self.prepare_features(transactions)
        df = self.engineer_advanced_features(df)
        
        # Ensure all required features are present
        missing_features = set(self.feature_columns) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0  # Fill missing features with 0
        
        X = df[self.feature_columns].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        results = []
        
        for i, transaction in enumerate(transactions):
            result = {
                'transaction_id': transaction.get('id', f'unknown_{i}'),
                'timestamp': transaction.get('timestamp', datetime.now().isoformat())
            }
            
            # Anomaly detection score
            anomaly_score = self.anomaly_model.decision_function([X_scaled[i]])[0]
            anomaly_prediction = self.anomaly_model.predict([X_scaled[i]])[0]
            
            # Convert anomaly score to probability (0-1 scale)
            anomaly_prob = max(0, min(1, (0.5 - anomaly_score) / 1.0))
            
            result.update({
                'anomaly_score': float(anomaly_score),
                'anomaly_probability': float(anomaly_prob),
                'is_anomaly': bool(anomaly_prediction == -1)
            })
            
            # Supervised model prediction if available
            if self.classification_model is not None:
                fraud_prob = self.classification_model.predict_proba([X_scaled[i]])[0]
                fraud_prediction = self.classification_model.predict([X_scaled[i]])[0]
                
                result.update({
                    'fraud_probability': float(fraud_prob[1]),  # Probability of fraud class
                    'legitimate_probability': float(fraud_prob[0]),
                    'predicted_fraud': bool(fraud_prediction == 1)
                })
                
                # Combined score (weighted average)
                combined_score = 0.6 * fraud_prob[1] + 0.4 * anomaly_prob
                result['combined_fraud_probability'] = float(combined_score)
            else:
                result['combined_fraud_probability'] = float(anomaly_prob)
            
            # Feature importance for this prediction
            if self.classification_model is not None:
                feature_contributions = {}
                for j, feature in enumerate(self.feature_columns):
                    importance = self.classification_model.feature_importances_[j]
                    value = X.iloc[i, j]
                    feature_contributions[feature] = {
                        'value': float(value),
                        'importance': float(importance),
                        'contribution': float(importance * abs(value))
                    }
                
                # Top contributing features
                top_features = sorted(
                    feature_contributions.items(),
                    key=lambda x: x[1]['contribution'],
                    reverse=True
                )[:5]
                
                result['top_risk_factors'] = [
                    {
                        'feature': feature,
                        'value': data['value'],
                        'contribution': data['contribution']
                    }
                    for feature, data in top_features
                ]
            
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about the trained models."""
        if not self.is_trained:
            return {'status': 'not_trained'}
        
        info = {
            'status': 'trained',
            'feature_count': len(self.feature_columns),
            'features': self.feature_columns,
            'anomaly_model': 'IsolationForest',
            'has_supervised_model': self.classification_model is not None
        }
        
        if self.classification_model is not None:
            info.update({
                'supervised_model': 'RandomForestClassifier',
                'n_estimators': self.classification_model.n_estimators,
                'feature_importance': dict(zip(
                    self.feature_columns,
                    self.classification_model.feature_importances_
                ))
            })
        
        return info
    
    def _save_models(self):
        """Save trained models to disk."""
        try:
            if self.anomaly_model is not None:
                joblib.dump(self.anomaly_model, os.path.join(self.model_path, 'anomaly_model.pkl'))
            
            if self.classification_model is not None:
                joblib.dump(self.classification_model, os.path.join(self.model_path, 'classification_model.pkl'))
            
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            joblib.dump(self.feature_columns, os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def _load_models(self):
        """Load trained models from disk."""
        try:
            anomaly_path = os.path.join(self.model_path, 'anomaly_model.pkl')
            classification_path = os.path.join(self.model_path, 'classification_model.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            features_path = os.path.join(self.model_path, 'feature_columns.pkl')
            
            if os.path.exists(scaler_path) and os.path.exists(features_path):
                self.scaler = joblib.load(scaler_path)
                self.feature_columns = joblib.load(features_path)
                
                if os.path.exists(anomaly_path):
                    self.anomaly_model = joblib.load(anomaly_path)
                
                if os.path.exists(classification_path):
                    self.classification_model = joblib.load(classification_path)
                
                if self.anomaly_model is not None:
                    self.is_trained = True
                    logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load existing models: {str(e)}")
    
    def generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[List[Dict], List[int]]:
        """
        Generate synthetic training data for demonstration purposes.
        In production, this would be replaced with real historical data.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Tuple of (transactions, labels)
        """
        np.random.seed(42)
        
        transactions = []
        labels = []
        
        for i in range(n_samples):
            # Generate base transaction
            is_fraud = np.random.random() < 0.1  # 10% fraud rate
            
            if is_fraud:
                # Fraudulent transaction patterns
                amount = np.random.lognormal(8, 2)  # Higher amounts
                hour = np.random.choice([2, 3, 4, 23])  # Unusual hours
                merchant = np.random.choice(['UNKNOWN MERCHANT', 'CASH ADVANCE', 'ATM WITHDRAWAL'])
                location = np.random.choice(['Unknown Location', 'High Risk Country', 'Offshore'])
            else:
                # Legitimate transaction patterns
                amount = np.random.lognormal(4, 1.5)  # Normal amounts
                hour = np.random.choice(range(6, 23))  # Normal hours
                merchant = np.random.choice(['GROCERY STORE', 'GAS STATION', 'RESTAURANT', 'RETAIL STORE'])
                location = np.random.choice(['New York, US', 'Los Angeles, US', 'Chicago, US'])
            
            transaction = {
                'id': f'TXN_{i:06d}',
                'amount': round(amount, 2),
                'merchant': merchant,
                'location': location,
                'timestamp': datetime.now().replace(
                    hour=hour,
                    minute=np.random.randint(0, 60),
                    second=np.random.randint(0, 60)
                ).isoformat(),
                'card_number': f'****{np.random.randint(1000, 9999)}'
            }
            
            transactions.append(transaction)
            labels.append(1 if is_fraud else 0)
        
        return transactions, labels
