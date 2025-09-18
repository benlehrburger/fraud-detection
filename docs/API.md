# FinTechCo Fraud Detection API Documentation

## Overview

The FinTechCo Fraud Detection API provides real-time transaction analysis, risk scoring, and fraud detection capabilities. The API is built with Flask and offers comprehensive endpoints for transaction validation, risk assessment, and machine learning-powered fraud detection.

**Base URL:** `http://localhost:5000`

**Content-Type:** `application/json`

## Authentication

Currently, the API operates without authentication for development purposes. In production, implement proper API key authentication or OAuth 2.0.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

## Endpoints

### Health Check

#### GET /health

Check the health status of the fraud detection service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "fraud_detection": "active",
    "risk_scoring": "active",
    "transaction_validator": "active",
    "ml_model": "trained"
  }
}
```

---

### Transactions

#### GET /api/transactions

Retrieve transactions with optional filtering and pagination.

**Query Parameters:**
- `page` (integer, optional) - Page number (default: 1)
- `per_page` (integer, optional) - Items per page (default: 50, max: 100)
- `risk_level` (string, optional) - Filter by risk level: `block`, `review`, `monitor`, `approve`

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": "TXN_001234",
      "timestamp": "2024-01-01T12:00:00Z",
      "amount": 150.00,
      "merchant": "Amazon.com",
      "location": "Seattle, WA, US",
      "card_number": "****1234",
      "fraud_analysis": {
        "risk_score": 0.3,
        "risk_level": "LOW",
        "factors": ["high_amount"]
      },
      "risk_analysis": {
        "risk_score": 0.25,
        "risk_level": "LOW",
        "confidence": 0.85,
        "factors": [
          {
            "name": "amount_anomaly",
            "weight": 0.25,
            "value": 0.2,
            "description": "Amount within normal range"
          }
        ],
        "recommendations": ["Log for pattern analysis"]
      },
      "final_decision": {
        "final_risk_score": 0.275,
        "action": "APPROVE",
        "reason": "Low fraud risk",
        "confidence": 0.85
      },
      "ml_prediction": {
        "fraud_probability": 0.15,
        "combined_fraud_probability": 0.22,
        "is_anomaly": false,
        "top_risk_factors": [
          {
            "feature": "amount",
            "value": 150.0,
            "contribution": 0.1
          }
        ]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1250,
    "pages": 25
  }
}
```

#### POST /api/transactions

Analyze a single transaction for fraud indicators.

**Request Body:**
```json
{
  "id": "TXN_001234",
  "amount": 150.00,
  "merchant": "Amazon.com",
  "location": "Seattle, WA, US",
  "timestamp": "2024-01-01T12:00:00Z",
  "card_number": "****1234",
  "currency": "USD",
  "description": "Online purchase"
}
```

**Required Fields:**
- `id` - Unique transaction identifier
- `amount` - Transaction amount (number or string)
- `merchant` - Merchant name
- `location` - Transaction location
- `timestamp` - ISO 8601 timestamp
- `card_number` - Masked card number (e.g., "****1234")

**Optional Fields:**
- `currency` - Currency code (default: "USD")
- `description` - Transaction description

**Response:**
Returns the same transaction object structure as GET /api/transactions, with complete analysis results.

#### POST /api/transactions/batch

Analyze multiple transactions in a single request.

**Request Body:**
```json
{
  "transactions": [
    {
      "id": "TXN_001234",
      "amount": 150.00,
      "merchant": "Amazon.com",
      "location": "Seattle, WA, US",
      "timestamp": "2024-01-01T12:00:00Z",
      "card_number": "****1234"
    },
    {
      "id": "TXN_001235",
      "amount": 25.50,
      "merchant": "Starbucks",
      "location": "New York, NY, US",
      "timestamp": "2024-01-01T12:05:00Z",
      "card_number": "****5678"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "transaction_index": 0,
      "transaction_id": "TXN_001234",
      "fraud_analysis": { /* ... */ },
      "validation_warnings": []
    },
    {
      "transaction_index": 1,
      "error": "Validation failed",
      "validation_errors": ["Invalid amount format"]
    }
  ],
  "summary": {
    "total_processed": 2,
    "successful": 1,
    "failed": 1,
    "validation_summary": {
      "total_transactions": 2,
      "valid_transactions": 1,
      "invalid_transactions": 1,
      "validation_rate": 50.0
    }
  }
}
```

---

### Alerts

#### GET /api/alerts

Retrieve fraud alerts with optional filtering.

**Query Parameters:**
- `severity` (string, optional) - Filter by severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `limit` (integer, optional) - Maximum number of alerts (default: 100)

**Response:**
```json
{
  "alerts": [
    {
      "id": "ALERT_000001",
      "transaction_id": "TXN_001234",
      "severity": "HIGH",
      "risk_score": 0.85,
      "action_required": "REVIEW",
      "reason": "High fraud risk detected",
      "merchant": "Unknown Merchant",
      "amount": 5000.00,
      "location": "High Risk Country",
      "created_at": "2024-01-01T12:00:00Z",
      "status": "OPEN"
    }
  ],
  "total_count": 15
}
```

---

### Statistics

#### GET /api/stats

Get fraud detection system statistics.

**Response:**
```json
{
  "total_transactions": 12500,
  "fraud_rate": 2.3,
  "risk_distribution": {
    "LOW": 10250,
    "MEDIUM": 1875,
    "HIGH": 312,
    "CRITICAL": 63
  },
  "alerts_count": 45,
  "model_status": "trained"
}
```

---

### Machine Learning Model

#### GET /api/model/info

Get information about the ML model.

**Response:**
```json
{
  "status": "trained",
  "feature_count": 15,
  "features": [
    "amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "merchant_length",
    "location_length"
  ],
  "anomaly_model": "IsolationForest",
  "has_supervised_model": true,
  "supervised_model": "RandomForestClassifier",
  "n_estimators": 100,
  "feature_importance": {
    "amount": 0.25,
    "hour": 0.15,
    "merchant_length": 0.12
  }
}
```

#### POST /api/model/train

Train or retrain the ML model.

**Request Body (Optional):**
```json
{
  "transactions": [
    {
      "id": "TXN_001",
      "amount": 100.0,
      "merchant": "Store",
      "location": "City, Country",
      "timestamp": "2024-01-01T12:00:00Z",
      "card_number": "****1234"
    }
  ],
  "labels": [0, 1, 0, 1]
}
```

If no training data is provided, the system will generate synthetic data for demonstration.

**Response:**
```json
{
  "status": "success",
  "message": "Model training completed",
  "training_results": {
    "feature_count": 15,
    "training_samples": 1000,
    "supervised_model_trained": true,
    "test_accuracy": 0.95,
    "classification_report": {
      "0": {
        "precision": 0.96,
        "recall": 0.98,
        "f1-score": 0.97
      },
      "1": {
        "precision": 0.89,
        "recall": 0.85,
        "f1-score": 0.87
      }
    }
  }
}
```

---

## Data Models

### Transaction Object

```typescript
interface Transaction {
  transaction_id: string;
  timestamp: string;
  amount: number;
  merchant: string;
  location: string;
  card_number: string;
  fraud_analysis?: {
    risk_score: number;
    risk_level: string;
    factors: string[];
  };
  risk_analysis?: {
    risk_score: number;
    risk_level: string;
    confidence: number;
    recommendations: string[];
    factors: Array<{
      name: string;
      weight: number;
      value: number;
      description: string;
    }>;
  };
  final_decision?: {
    final_risk_score: number;
    action: string;
    reason: string;
    confidence: number;
  };
  ml_prediction?: {
    fraud_probability: number;
    combined_fraud_probability: number;
    is_anomaly: boolean;
    top_risk_factors?: Array<{
      feature: string;
      value: number;
      contribution: number;
    }>;
  };
  validation_warnings?: string[];
}
```

### Alert Object

```typescript
interface Alert {
  id: string;
  transaction_id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  action_required: string;
  reason: string;
  merchant: string;
  amount: number;
  location: string;
  created_at: string;
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
}
```

---

## Risk Levels

### Transaction Risk Levels
- **MINIMAL** (0.0 - 0.2) - Very low risk, normal transaction
- **LOW** (0.2 - 0.4) - Low risk, standard monitoring
- **MEDIUM** (0.4 - 0.6) - Medium risk, enhanced monitoring
- **HIGH** (0.6 - 0.8) - High risk, requires review
- **CRITICAL** (0.8 - 1.0) - Critical risk, block transaction

### Actions
- **APPROVE** - Allow transaction to proceed
- **MONITOR** - Allow but increase monitoring
- **REVIEW** - Hold for manual review
- **BLOCK** - Block transaction immediately

---

## Rate Limiting

Current implementation has no rate limiting. In production, implement:
- 1000 requests per hour per IP for GET endpoints
- 100 requests per hour per IP for POST endpoints
- 10 requests per hour for model training

---

## Examples

### Analyze a High-Risk Transaction

```bash
curl -X POST http://localhost:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "TXN_SUSPICIOUS_001",
    "amount": 15000.00,
    "merchant": "UNKNOWN MERCHANT",
    "location": "High Risk Country",
    "timestamp": "2024-01-01T03:00:00Z",
    "card_number": "****9999"
  }'
```

### Get Recent High-Risk Transactions

```bash
curl "http://localhost:5000/api/transactions?risk_level=review&per_page=10"
```

### Check System Health

```bash
curl http://localhost:5000/health
```

---

## WebSocket Support (Future)

Real-time transaction monitoring will be available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws/transactions');
ws.onmessage = (event) => {
  const transaction = JSON.parse(event.data);
  // Handle real-time transaction update
};
```

---

## Security Considerations

1. **Input Validation** - All inputs are validated and sanitized
2. **PCI DSS Compliance** - Card numbers must be masked
3. **Rate Limiting** - Implement in production
4. **Authentication** - Add API key or OAuth 2.0
5. **HTTPS** - Use TLS in production
6. **Audit Logging** - All transactions are logged

---

## Support

For API support and questions:
- Email: api-support@fintechco.com
- Documentation: https://docs.fintechco.com/fraud-detection
- Status Page: https://status.fintechco.com
