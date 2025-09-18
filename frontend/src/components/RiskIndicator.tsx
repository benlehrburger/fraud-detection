import React from 'react';
import './RiskIndicator.css';

interface RiskIndicatorProps {
  level: 'MINIMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'NORMAL';
  score?: number;
  confidence?: number;
  trends?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
  details?: {
    totalTransactions: number;
    flaggedTransactions: number;
    blockedTransactions: number;
  };
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({ 
  level, 
  score, 
  confidence, 
  trends,
  details 
}) => {
  const getRiskConfig = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case 'CRITICAL':
        return {
          color: '#e74c3c',
          bgColor: 'rgba(231, 76, 60, 0.1)',
          icon: '🚨',
          label: 'Critical Risk',
          description: 'Immediate action required',
          intensity: 100
        };
      case 'HIGH':
        return {
          color: '#f39c12',
          bgColor: 'rgba(243, 156, 18, 0.1)',
          icon: '⚠️',
          label: 'High Risk',
          description: 'Enhanced monitoring active',
          intensity: 80
        };
      case 'MEDIUM':
        return {
          color: '#f1c40f',
          bgColor: 'rgba(241, 196, 15, 0.1)',
          icon: '⚡',
          label: 'Medium Risk',
          description: 'Standard monitoring',
          intensity: 60
        };
      case 'LOW':
        return {
          color: '#27ae60',
          bgColor: 'rgba(39, 174, 96, 0.1)',
          icon: '✅',
          label: 'Low Risk',
          description: 'Normal activity',
          intensity: 30
        };
      case 'MINIMAL':
        return {
          color: '#2ecc71',
          bgColor: 'rgba(46, 204, 113, 0.1)',
          icon: '🛡️',
          label: 'Minimal Risk',
          description: 'All systems normal',
          intensity: 10
        };
      case 'NORMAL':
      default:
        return {
          color: '#3498db',
          bgColor: 'rgba(52, 152, 219, 0.1)',
          icon: '📊',
          label: 'Normal',
          description: 'System operating normally',
          intensity: 20
        };
    }
  };

  const config = getRiskConfig(level);

  const getTrendIcon = () => {
    if (!trends) return null;
    
    switch (trends.direction) {
      case 'up':
        return <span className="trend-icon trend-up">📈</span>;
      case 'down':
        return <span className="trend-icon trend-down">📉</span>;
      case 'stable':
      default:
        return <span className="trend-icon trend-stable">➡️</span>;
    }
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="risk-indicator" style={{ borderColor: config.color }}>
      <div className="risk-header">
        <div className="risk-icon-container">
          <span className="risk-icon" style={{ backgroundColor: config.bgColor }}>
            {config.icon}
          </span>
        </div>
        
        <div className="risk-info">
          <h3 className="risk-label" style={{ color: config.color }}>
            {config.label}
          </h3>
          <p className="risk-description">{config.description}</p>
        </div>

        {trends && (
          <div className="risk-trend">
            {getTrendIcon()}
            <span className="trend-value">
              {trends.percentage > 0 ? '+' : ''}{trends.percentage.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Risk Score Gauge */}
      {score !== undefined && (
        <div className="risk-gauge-container">
          <div className="risk-gauge">
            <div className="gauge-background">
              <div 
                className="gauge-fill"
                style={{ 
                  width: `${config.intensity}%`,
                  backgroundColor: config.color 
                }}
              ></div>
            </div>
            <div className="gauge-labels">
              <span className="gauge-label-left">0%</span>
              <span className="gauge-value" style={{ color: config.color }}>
                {formatPercentage(score)}
              </span>
              <span className="gauge-label-right">100%</span>
            </div>
          </div>
          
          {confidence !== undefined && (
            <div className="confidence-indicator">
              <span className="confidence-label">Confidence:</span>
              <span className="confidence-value">{formatPercentage(confidence)}</span>
              <div className="confidence-bar">
                <div 
                  className="confidence-fill"
                  style={{ width: `${confidence * 100}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Transaction Details */}
      {details && (
        <div className="risk-details">
          <div className="detail-row">
            <div className="detail-item">
              <span className="detail-label">Total Transactions</span>
              <span className="detail-value">{details.totalTransactions.toLocaleString()}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Flagged</span>
              <span className="detail-value flagged">{details.flaggedTransactions.toLocaleString()}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Blocked</span>
              <span className="detail-value blocked">{details.blockedTransactions.toLocaleString()}</span>
            </div>
          </div>
          
          {details.totalTransactions > 0 && (
            <div className="risk-breakdown">
              <div className="breakdown-bar">
                <div 
                  className="breakdown-segment safe"
                  style={{ 
                    width: `${((details.totalTransactions - details.flaggedTransactions) / details.totalTransactions) * 100}%` 
                  }}
                  title={`Safe: ${details.totalTransactions - details.flaggedTransactions} transactions`}
                ></div>
                <div 
                  className="breakdown-segment flagged"
                  style={{ 
                    width: `${((details.flaggedTransactions - details.blockedTransactions) / details.totalTransactions) * 100}%` 
                  }}
                  title={`Flagged: ${details.flaggedTransactions - details.blockedTransactions} transactions`}
                ></div>
                <div 
                  className="breakdown-segment blocked"
                  style={{ 
                    width: `${(details.blockedTransactions / details.totalTransactions) * 100}%` 
                  }}
                  title={`Blocked: ${details.blockedTransactions} transactions`}
                ></div>
              </div>
              <div className="breakdown-legend">
                <div className="legend-item">
                  <div className="legend-color safe"></div>
                  <span>Safe</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color flagged"></div>
                  <span>Flagged</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color blocked"></div>
                  <span>Blocked</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pulse Animation for Critical Risk */}
      {level.toUpperCase() === 'CRITICAL' && (
        <div className="critical-pulse" style={{ borderColor: config.color }}></div>
      )}
    </div>
  );
};
