import React, { useState, useMemo } from 'react';
import './TransactionList.css';

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
    top_risk_factors?: Array<{
      feature: string;
      value: number;
      contribution: number;
    }>;
  };
}

interface TransactionListProps {
  transactions: Transaction[];
  loading: boolean;
}

export const TransactionList: React.FC<TransactionListProps> = ({ transactions, loading }) => {
  const [sortField, setSortField] = useState<keyof Transaction>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  // Sort and filter transactions
  const filteredAndSortedTransactions = useMemo(() => {
    let filtered = transactions;

    // Apply risk level filter
    if (filterRisk !== 'all') {
      filtered = filtered.filter(t => 
        t.final_decision?.action?.toLowerCase() === filterRisk.toLowerCase() ||
        t.risk_analysis?.risk_level?.toLowerCase() === filterRisk.toLowerCase()
      );
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(t =>
        t.merchant.toLowerCase().includes(term) ||
        t.location.toLowerCase().includes(term) ||
        t.transaction_id.toLowerCase().includes(term) ||
        t.card_number.includes(term)
      );
    }

    // Sort transactions
    return filtered.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle nested properties
      if (sortField === 'timestamp') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [transactions, sortField, sortDirection, filterRisk, searchTerm]);

  const handleSort = (field: keyof Transaction) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getRiskLevelClass = (transaction: Transaction): string => {
    const riskLevel = transaction.final_decision?.action || transaction.risk_analysis?.risk_level || 'LOW';
    
    switch (riskLevel.toUpperCase()) {
      case 'BLOCK':
      case 'CRITICAL':
        return 'risk-critical';
      case 'REVIEW':
      case 'HIGH':
        return 'risk-high';
      case 'MONITOR':
      case 'MEDIUM':
        return 'risk-medium';
      case 'APPROVE':
      case 'LOW':
      default:
        return 'risk-low';
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const getRiskScore = (transaction: Transaction): number => {
    return transaction.final_decision?.final_risk_score || 
           transaction.risk_analysis?.risk_score || 
           transaction.fraud_analysis?.risk_score || 
           0;
  };

  if (loading) {
    return (
      <div className="transaction-list-loading">
        <div className="loading-spinner"></div>
        <p>Loading transactions...</p>
      </div>
    );
  }

  return (
    <div className="transaction-list">
      <div className="transaction-list-header">
        <h2>Transaction Monitoring</h2>
        
        <div className="transaction-controls">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="filter-controls">
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="risk-filter"
            >
              <option value="all">All Risk Levels</option>
              <option value="block">Blocked</option>
              <option value="review">Review Required</option>
              <option value="monitor">Monitor</option>
              <option value="approve">Approved</option>
            </select>
          </div>
        </div>
      </div>

      <div className="transaction-summary">
        <div className="summary-stat">
          <span className="stat-label">Total:</span>
          <span className="stat-value">{filteredAndSortedTransactions.length}</span>
        </div>
        <div className="summary-stat">
          <span className="stat-label">High Risk:</span>
          <span className="stat-value risk-high">
            {filteredAndSortedTransactions.filter(t => 
              ['BLOCK', 'REVIEW', 'HIGH', 'CRITICAL'].includes(
                (t.final_decision?.action || t.risk_analysis?.risk_level || '').toUpperCase()
              )
            ).length}
          </span>
        </div>
      </div>

      <div className="transaction-table-container">
        <table className="transaction-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('timestamp')} className="sortable">
                Time {sortField === 'timestamp' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('transaction_id')} className="sortable">
                ID {sortField === 'transaction_id' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('amount')} className="sortable">
                Amount {sortField === 'amount' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('merchant')} className="sortable">
                Merchant {sortField === 'merchant' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Location</th>
              <th>Card</th>
              <th>Risk Score</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedTransactions.map((transaction) => (
              <tr 
                key={transaction.transaction_id} 
                className={`transaction-row ${getRiskLevelClass(transaction)}`}
              >
                <td className="timestamp-cell">
                  {formatTimestamp(transaction.timestamp)}
                </td>
                <td className="id-cell">
                  <code>{transaction.transaction_id}</code>
                </td>
                <td className="amount-cell">
                  {formatCurrency(transaction.amount)}
                </td>
                <td className="merchant-cell">
                  {transaction.merchant}
                </td>
                <td className="location-cell">
                  {transaction.location}
                </td>
                <td className="card-cell">
                  <code>{transaction.card_number}</code>
                </td>
                <td className="risk-score-cell">
                  <div className="risk-score-container">
                    <span className="risk-score">
                      {(getRiskScore(transaction) * 100).toFixed(1)}%
                    </span>
                    {transaction.ml_prediction && (
                      <span className="ml-indicator" title="ML Enhanced">🤖</span>
                    )}
                  </div>
                </td>
                <td className="status-cell">
                  <span className={`status-badge ${getRiskLevelClass(transaction)}`}>
                    {transaction.final_decision?.action || 
                     transaction.risk_analysis?.risk_level || 
                     'PENDING'}
                  </span>
                </td>
                <td className="actions-cell">
                  <button
                    onClick={() => setSelectedTransaction(transaction)}
                    className="details-button"
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAndSortedTransactions.length === 0 && (
          <div className="no-transactions">
            <p>No transactions found matching your criteria.</p>
          </div>
        )}
      </div>

      {/* Transaction Details Modal */}
      {selectedTransaction && (
        <div className="modal-overlay" onClick={() => setSelectedTransaction(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Transaction Details</h3>
              <button 
                className="modal-close"
                onClick={() => setSelectedTransaction(null)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <h4>Basic Information</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>Transaction ID:</label>
                    <span>{selectedTransaction.transaction_id}</span>
                  </div>
                  <div className="detail-item">
                    <label>Amount:</label>
                    <span>{formatCurrency(selectedTransaction.amount)}</span>
                  </div>
                  <div className="detail-item">
                    <label>Merchant:</label>
                    <span>{selectedTransaction.merchant}</span>
                  </div>
                  <div className="detail-item">
                    <label>Location:</label>
                    <span>{selectedTransaction.location}</span>
                  </div>
                  <div className="detail-item">
                    <label>Card:</label>
                    <span>{selectedTransaction.card_number}</span>
                  </div>
                  <div className="detail-item">
                    <label>Time:</label>
                    <span>{formatTimestamp(selectedTransaction.timestamp)}</span>
                  </div>
                </div>
              </div>

              {selectedTransaction.final_decision && (
                <div className="detail-section">
                  <h4>Final Decision</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Action:</label>
                      <span className={`status-badge ${getRiskLevelClass(selectedTransaction)}`}>
                        {selectedTransaction.final_decision.action}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Risk Score:</label>
                      <span>{(selectedTransaction.final_decision.final_risk_score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="detail-item">
                      <label>Confidence:</label>
                      <span>{(selectedTransaction.final_decision.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="detail-item full-width">
                      <label>Reason:</label>
                      <span>{selectedTransaction.final_decision.reason}</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedTransaction.risk_analysis && (
                <div className="detail-section">
                  <h4>Risk Analysis</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Risk Level:</label>
                      <span>{selectedTransaction.risk_analysis.risk_level}</span>
                    </div>
                    <div className="detail-item">
                      <label>Risk Score:</label>
                      <span>{(selectedTransaction.risk_analysis.risk_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  
                  {selectedTransaction.risk_analysis.recommendations && 
                   selectedTransaction.risk_analysis.recommendations.length > 0 && (
                    <div className="recommendations">
                      <label>Recommendations:</label>
                      <ul>
                        {selectedTransaction.risk_analysis.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {selectedTransaction.ml_prediction && (
                <div className="detail-section">
                  <h4>ML Prediction</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Fraud Probability:</label>
                      <span>{(selectedTransaction.ml_prediction.fraud_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="detail-item">
                      <label>Combined Score:</label>
                      <span>{(selectedTransaction.ml_prediction.combined_fraud_probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {selectedTransaction.ml_prediction.top_risk_factors && (
                    <div className="risk-factors">
                      <label>Top Risk Factors:</label>
                      <div className="risk-factors-list">
                        {selectedTransaction.ml_prediction.top_risk_factors.map((factor, index) => (
                          <div key={index} className="risk-factor-item">
                            <span className="factor-name">{factor.feature}</span>
                            <span className="factor-value">{factor.value.toFixed(2)}</span>
                            <div className="factor-contribution">
                              <div 
                                className="contribution-bar"
                                style={{ width: `${Math.min(factor.contribution * 100, 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
