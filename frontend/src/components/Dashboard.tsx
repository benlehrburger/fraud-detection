import React from 'react';
import { TransactionList } from './TransactionList';
import { RiskIndicator } from './RiskIndicator';
import { Transaction, Alert, Statistics } from '../services/api';
import './Dashboard.css';

interface DashboardProps {
  transactions: Transaction[];
  alerts: Alert[];
  statistics: Statistics | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ 
  transactions, 
  alerts, 
  statistics, 
  loading, 
  onRefresh 
}) => {
  // Calculate risk metrics
  const highRiskTransactions = transactions.filter(t => 
    ['BLOCK', 'REVIEW', 'HIGH', 'CRITICAL'].includes(
      (t.final_decision?.action || t.risk_analysis?.risk_level || '').toUpperCase()
    )
  );

  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL');
  const highAlerts = alerts.filter(a => a.severity === 'HIGH');

  // Determine overall risk level
  const getOverallRiskLevel = (): 'MINIMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' => {
    if (criticalAlerts.length > 0) return 'CRITICAL';
    if (highAlerts.length > 2) return 'HIGH';
    if (highRiskTransactions.length > 5) return 'MEDIUM';
    if (highRiskTransactions.length > 0) return 'LOW';
    return 'MINIMAL';
  };

  const overallRiskLevel = getOverallRiskLevel();
  const fraudRate = statistics?.fraud_rate || 0;

  return (
    <div className="dashboard">

      {/* Key Metrics Grid */}
      <div className="metrics-grid" style={{ paddingTop: '30px' }}>
        <div className="metric-card">
          <div className="metric-header">
            <h3>Total Transactions</h3>
            <span className="metric-icon">📊</span>
          </div>
          <p className="metric-value">{statistics?.total_transactions.toLocaleString() || 0}</p>
          <p className="metric-change">Last 24 hours</p>
        </div>
        
        <div className="metric-card alert">
          <div className="metric-header">
            <h3>High Risk</h3>
            <span className="metric-icon">⚠️</span>
          </div>
          <p className="metric-value">{highRiskTransactions.length}</p>
          <p className="metric-change">
            {fraudRate > 0 ? `${fraudRate.toFixed(1)}% fraud rate` : 'No fraud detected'}
          </p>
        </div>
        
        <div className="metric-card">
          <div className="metric-header">
            <h3>Active Alerts</h3>
            <span className="metric-icon">🚨</span>
          </div>
          <p className="metric-value">{alerts.length}</p>
          <p className="metric-change">
            {criticalAlerts.length} critical, {highAlerts.length} high
          </p>
        </div>
        
        <div className="metric-card">
          <div className="metric-header">
            <h3>ML Status</h3>
            <span className="metric-icon">🤖</span>
          </div>
          <p className="metric-value">
            {statistics?.model_status === 'trained' ? 'Active' : 'Training'}
          </p>
          <p className="metric-change">
            {statistics?.model_status === 'trained' ? 'ML Enhanced' : 'Basic Rules'}
          </p>
        </div>
      </div>

      {/* Risk Indicator */}
      <div className="risk-section">
        <RiskIndicator 
          level={overallRiskLevel}
          score={fraudRate / 100}
          confidence={0.85}
          trends={{
            direction: fraudRate > 2 ? 'up' : fraudRate < 1 ? 'down' : 'stable',
            percentage: fraudRate
          }}
          details={{
            totalTransactions: statistics?.total_transactions || 0,
            flaggedTransactions: highRiskTransactions.length,
            blockedTransactions: transactions.filter(t => 
              t.final_decision?.action === 'BLOCK'
            ).length
          }}
        />
      </div>

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <div className="section-header">
            <h2>Recent Alerts</h2>
            <span className="alert-count">{alerts.length} active</span>
          </div>
          
          <div className="alerts-list">
            {alerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className={`alert-item severity-${alert.severity.toLowerCase()}`}>
                <div className="alert-info">
                  <div className="alert-title">
                    <span className="alert-severity">{alert.severity}</span>
                    <span className="alert-id">#{alert.id}</span>
                  </div>
                  <p className="alert-reason">{alert.reason}</p>
                  <div className="alert-details">
                    <span>{alert.merchant}</span>
                    <span>${alert.amount.toLocaleString()}</span>
                    <span>{new Date(alert.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
                <div className="alert-actions">
                  <button className="alert-btn primary">Investigate</button>
                  <button className="alert-btn secondary">Dismiss</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction List */}
      <div className="transactions-section">
        <TransactionList 
          transactions={transactions}
          loading={loading}
        />
      </div>
    </div>
  );
};