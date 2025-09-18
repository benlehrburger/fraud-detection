import React, { useState, useEffect, useCallback } from 'react';
import { Dashboard } from './components/Dashboard';
import { apiService, Transaction, Alert, Statistics, ApiError } from './services/api';
import './App.css';

interface AppState {
  transactions: Transaction[];
  alerts: Alert[];
  statistics: Statistics | null;
  loading: boolean;
  error: string | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    transactions: [],
    alerts: [],
    statistics: {
      total_transactions: 0,
      fraud_rate: 0,
      risk_distribution: {},
      alerts_count: 0,
      model_status: 'not_trained'
    },
    loading: false,
    error: null,
    connectionStatus: 'connected'
  });

  const [showDemoPanel, setShowDemoPanel] = useState(false);
  const [pollingCleanup, setPollingCleanup] = useState<(() => void) | null>(null);

  // Update state helper
  const updateState = useCallback((updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Error handler
  const handleError = useCallback((error: unknown, context: string) => {
    console.error(`Error in ${context}:`, error);
    console.error('Error details:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      status: error instanceof ApiError ? error.status : undefined
    });
    
    let errorMessage = 'An unexpected error occurred';
    
    if (error instanceof ApiError) {
      errorMessage = `API Error: ${error.message}`;
      if (error.status === 0) {
        updateState({ connectionStatus: 'disconnected' });
        errorMessage = 'Unable to connect to fraud detection service';
      }
    } else if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    updateState({ error: errorMessage, loading: false });
  }, [updateState]);

  // Initialize application
  const initializeApp = useCallback(async () => {
    console.log('Starting app initialization...');
    updateState({ loading: true, error: null, connectionStatus: 'connecting' });
    
    try {
      // Test connection with service discovery
      console.log('Discovering and testing connection to backend...');
      const isConnected = await apiService.testConnection(5); // More retries for initial connection
      console.log('Connection test result:', isConnected);
      
      if (!isConnected) {
        throw new Error('Cannot connect to fraud detection service. Please ensure the backend is running.');
      }
      
      console.log('Connection successful, updating state...');
      updateState({ connectionStatus: 'connected' });
      
      // Load initial data in parallel
      console.log('Loading initial data...');
      const [transactionsResponse, alertsResponse, statisticsResponse] = await Promise.allSettled([
        apiService.fetchTransactions({ per_page: 100 }),
        apiService.fetchAlerts({ limit: 50 }),
        apiService.fetchStatistics()
      ]);
      
      console.log('API responses:', {
        transactions: transactionsResponse.status,
        alerts: alertsResponse.status,
        statistics: statisticsResponse.status
      });
      
      // Process results
      const transactions = transactionsResponse.status === 'fulfilled' 
        ? transactionsResponse.value.transactions 
        : [];
        
      const alerts = alertsResponse.status === 'fulfilled' 
        ? alertsResponse.value.alerts 
        : [];
        
      const statistics = statisticsResponse.status === 'fulfilled' 
        ? statisticsResponse.value 
        : null;
      
      console.log('Processed data:', { 
        transactionCount: transactions.length, 
        alertCount: alerts.length, 
        hasStatistics: !!statistics 
      });
      
      updateState({
        transactions,
        alerts,
        statistics,
        loading: false,
        error: null
      });
      
      console.log('App initialization completed successfully!');
      
      // Start real-time polling
      const cleanup = apiService.startPolling((newTransactions) => {
        updateState({ transactions: newTransactions });
      }, 10000); // Poll every 10 seconds
      
      setPollingCleanup(() => cleanup);
      
    } catch (error) {
      handleError(error, 'initialization');
    }
  }, [updateState, handleError]);

  // Refresh data
  const refreshData = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });
      
      const [transactionsResponse, alertsResponse, statisticsResponse] = await Promise.all([
        apiService.fetchTransactions({ per_page: 100 }),
        apiService.fetchAlerts({ limit: 50 }),
        apiService.fetchStatistics()
      ]);
      
      updateState({
        transactions: transactionsResponse.transactions,
        alerts: alertsResponse.alerts,
        statistics: statisticsResponse,
        loading: false
      });
      
    } catch (error) {
      handleError(error, 'data refresh');
    }
  }, [updateState, handleError]);

  // Submit demo transaction
  const submitDemoTransaction = useCallback(async () => {
    try {
      const demoTransaction = apiService.generateDemoTransaction();
      
      updateState({ loading: true, error: null });
      
      const result = await apiService.analyzeTransaction(demoTransaction);
      
      // Add to transactions list
      updateState({
        transactions: [result, ...state.transactions],
        loading: false
      });
      
      // Refresh statistics
      const newStats = await apiService.fetchStatistics();
      updateState({ statistics: newStats });
      
    } catch (error) {
      handleError(error, 'demo transaction submission');
    }
  }, [state.transactions, updateState, handleError]);

  // Submit batch demo transactions
  const submitBatchDemoTransactions = useCallback(async (count: number = 5) => {
    try {
      const demoTransactions = apiService.generateDemoTransactions(count);
      
      updateState({ loading: true, error: null });
      
      const result = await apiService.analyzeBatchTransactions(demoTransactions);
      
      // Add successful transactions to list
      const successfulTransactions = result.results.filter(
        (r): r is Transaction => !('error' in r)
      );
      
      updateState({
        transactions: [...successfulTransactions, ...state.transactions],
        loading: false
      });
      
      // Refresh statistics
      const newStats = await apiService.fetchStatistics();
      updateState({ statistics: newStats });
      
    } catch (error) {
      handleError(error, 'batch demo transaction submission');
    }
  }, [state.transactions, updateState, handleError]);

  // Train ML model
  const trainModel = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });
      
      const result = await apiService.trainModel();
      
      updateState({ loading: false });
      
      // Show success message
      alert(`Model training completed: ${result.message}`);
      
      // Refresh statistics to show updated model status
      const newStats = await apiService.fetchStatistics();
      updateState({ statistics: newStats });
      
    } catch (error) {
      handleError(error, 'model training');
    }
  }, [updateState, handleError]);

  // Load initial data on mount (optional - can be triggered by user)
  useEffect(() => {
    // Skip automatic initialization - let user trigger data loading
    console.log('App loaded - ready for user interaction');
  }, []);

  // Connection status indicator
  const ConnectionStatus: React.FC = () => (
    <div className={`connection-status ${state.connectionStatus}`}>
      <div className="status-indicator"></div>
      <span className="status-text">
        {state.connectionStatus === 'connected' && 'Connected'}
        {state.connectionStatus === 'connecting' && 'Connecting...'}
        {state.connectionStatus === 'disconnected' && 'Disconnected'}
      </span>
    </div>
  );

  // Error display
  const ErrorDisplay: React.FC = () => (
    state.error ? (
      <div className="error-banner">
        <div className="error-content">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{state.error}</span>
          <button 
            className="error-retry"
            onClick={initializeApp}
          >
            Retry
          </button>
        </div>
      </div>
    ) : null
  );

  // Demo panel
  const DemoPanel: React.FC = () => (
    showDemoPanel ? (
      <div className="demo-panel">
        <div className="demo-header">
          <h3>Demo Controls</h3>
          <button 
            className="demo-close"
            onClick={() => setShowDemoPanel(false)}
          >
            ×
          </button>
        </div>
        <div className="demo-actions">
          <button 
            className="demo-button"
            onClick={submitDemoTransaction}
            disabled={state.loading}
          >
            Submit Demo Transaction
          </button>
          <button 
            className="demo-button"
            onClick={() => submitBatchDemoTransactions(5)}
            disabled={state.loading}
          >
            Submit 5 Demo Transactions
          </button>
          <button 
            className="demo-button"
            onClick={trainModel}
            disabled={state.loading}
          >
            Train ML Model
          </button>
          <button 
            className="demo-button secondary"
            onClick={refreshData}
            disabled={state.loading}
          >
            Refresh Data
          </button>
        </div>
      </div>
    ) : null
  );

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="app-title">
              <span className="title-icon">🛡️</span>
              FinTechCo Fraud Detection
            </h1>
            <p className="app-subtitle">Real-time Transaction Monitoring & Risk Assessment</p>
          </div>
          
          <div className="header-right">
            <ConnectionStatus />
            
            <button 
              className="demo-toggle"
              onClick={() => setShowDemoPanel(!showDemoPanel)}
              title="Demo Controls"
            >
              🧪 Demo
            </button>
            
            <button 
              className="refresh-button"
              onClick={refreshData}
              disabled={state.loading}
              title="Refresh Data"
            >
              🔄
            </button>
          </div>
        </div>
      </header>

      <ErrorDisplay />
      <DemoPanel />

      <main className="app-main">
        <Dashboard 
          transactions={state.transactions}
          alerts={state.alerts}
          statistics={state.statistics}
          loading={state.loading}
          onRefresh={refreshData}
        />
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-left">
            <p>&copy; 2025 FinTechCo. All rights reserved.</p>
            <p>Fraud Detection System v2.0</p>
          </div>
          <div className="footer-right">
            <span className="footer-stats">
              {state.statistics && (
                <>
                  {state.statistics.total_transactions.toLocaleString()} transactions monitored
                  {state.statistics.model_status === 'trained' && ' • ML Enhanced'}
                </>
              )}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
