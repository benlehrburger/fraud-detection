// Use relative URLs in development (React proxy) and configurable URL in production
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? (process.env.REACT_APP_API_URL || '/api')
  : '';

export interface Transaction {
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

export interface Alert {
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

export interface Statistics {
  total_transactions: number;
  fraud_rate: number;
  risk_distribution: Record<string, number>;
  alerts_count: number;
  model_status: 'trained' | 'not_trained';
}

export interface ModelInfo {
  status: 'trained' | 'not_trained';
  feature_count?: number;
  features?: string[];
  anomaly_model?: string;
  has_supervised_model?: boolean;
  supervised_model?: string;
  n_estimators?: number;
  feature_importance?: Record<string, number>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiService {
  protected baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  protected async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const config = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.error || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response.text() as unknown as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error occurred',
        0
      );
    }
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    services: Record<string, string>;
  }> {
    return this.request('/health');
  }

  // Transaction endpoints
  async fetchTransactions(params?: {
    page?: number;
    per_page?: number;
    risk_level?: string;
  }): Promise<{
    transactions: Transaction[];
    pagination: {
      page: number;
      per_page: number;
      total: number;
      pages: number;
    };
  }> {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.per_page) searchParams.append('per_page', params.per_page.toString());
    if (params?.risk_level) searchParams.append('risk_level', params.risk_level);

    const queryString = searchParams.toString();
    const endpoint = `/api/transactions${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  async analyzeTransaction(transactionData: {
    id: string;
    amount: number | string;
    merchant: string;
    location: string;
    timestamp: string;
    card_number: string;
    currency?: string;
    description?: string;
  }): Promise<Transaction> {
    return this.request('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(transactionData),
    });
  }

  async analyzeBatchTransactions(transactions: Array<{
    id: string;
    amount: number | string;
    merchant: string;
    location: string;
    timestamp: string;
    card_number: string;
    currency?: string;
    description?: string;
  }>): Promise<{
    results: Array<Transaction | { error: string; transaction_index: number }>;
    summary: {
      total_processed: number;
      successful: number;
      failed: number;
      validation_summary: any;
    };
  }> {
    return this.request('/api/transactions/batch', {
      method: 'POST',
      body: JSON.stringify({ transactions }),
    });
  }

  // Alert endpoints
  async fetchAlerts(params?: {
    severity?: string;
    limit?: number;
  }): Promise<{
    alerts: Alert[];
    total_count: number;
  }> {
    const searchParams = new URLSearchParams();
    
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/alerts${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  // Statistics endpoint
  async fetchStatistics(): Promise<Statistics> {
    return this.request('/api/stats');
  }

  // ML Model endpoints
  async getModelInfo(): Promise<ModelInfo> {
    return this.request('/api/model/info');
  }

  async trainModel(trainingData?: {
    transactions: any[];
    labels: number[];
  }): Promise<{
    status: string;
    message: string;
    training_results: any;
  }> {
    return this.request('/api/model/train', {
      method: 'POST',
      body: trainingData ? JSON.stringify(trainingData) : undefined,
    });
  }

  // Utility methods with retry logic
  async testConnection(maxRetries: number = 3): Promise<boolean> {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        await this.healthCheck();
        return true;
      } catch (error) {
        console.warn(`Connection attempt ${attempt}/${maxRetries} failed:`, error);
        if (attempt < maxRetries) {
          // Exponential backoff: 1s, 2s, 4s
          const delay = Math.pow(2, attempt - 1) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    return false;
  }

  // Service discovery - check multiple possible backend URLs
  async discoverService(): Promise<string | null> {
    const possibleUrls = [
      '', // Current origin (proxy)
      'http://localhost:5001',
      'http://localhost:5000',
      'http://127.0.0.1:5001',
      'http://127.0.0.1:5000'
    ];

    for (const url of possibleUrls) {
      try {
        const testService = new ApiService(url);
        const isHealthy = await testService.testConnection(1);
        if (isHealthy) {
          console.log(`Service discovered at: ${url || 'current origin'}`);
          return url;
        }
      } catch {
        // Continue to next URL
      }
    }
    
    return null;
  }

  // Real-time updates (WebSocket simulation with polling)
  startPolling(
    callback: (transactions: Transaction[]) => void,
    interval: number = 5000
  ): () => void {
    const poll = async () => {
      try {
        const response = await this.fetchTransactions({ per_page: 50 });
        callback(response.transactions);
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    // Initial fetch
    poll();

    // Set up interval
    const intervalId = setInterval(poll, interval);

    // Return cleanup function
    return () => clearInterval(intervalId);
  }

  // Generate demo transaction for testing
  generateDemoTransaction(): {
    id: string;
    amount: number;
    merchant: string;
    location: string;
    timestamp: string;
    card_number: string;
  } {
    const merchants = [
      'Amazon.com',
      'Starbucks Coffee',
      'Shell Gas Station',
      'Walmart Supercenter',
      'McDonald\'s',
      'Target Store',
      'CVS Pharmacy',
      'Home Depot',
      'Uber Technologies',
      'Netflix.com'
    ];

    const locations = [
      'New York, NY, US',
      'Los Angeles, CA, US',
      'Chicago, IL, US',
      'Houston, TX, US',
      'Phoenix, AZ, US',
      'Philadelphia, PA, US',
      'San Antonio, TX, US',
      'San Diego, CA, US',
      'Dallas, TX, US',
      'San Jose, CA, US'
    ];

    const cardNumbers = [
      '****1234',
      '****5678',
      '****9012',
      '****3456',
      '****7890'
    ];

    return {
      id: `TXN_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      amount: Math.round((Math.random() * 500 + 10) * 100) / 100,
      merchant: merchants[Math.floor(Math.random() * merchants.length)],
      location: locations[Math.floor(Math.random() * locations.length)],
      timestamp: new Date().toISOString(),
      card_number: cardNumbers[Math.floor(Math.random() * cardNumbers.length)]
    };
  }

  // Batch demo transaction generation
  generateDemoTransactions(count: number = 10): Array<{
    id: string;
    amount: number;
    merchant: string;
    location: string;
    timestamp: string;
    card_number: string;
  }> {
    return Array.from({ length: count }, () => this.generateDemoTransaction());
  }
}

// Create and export singleton instance
export const apiService = new ApiService();

// Export individual functions for convenience
export const {
  healthCheck,
  fetchTransactions,
  analyzeTransaction,
  analyzeBatchTransactions,
  fetchAlerts,
  fetchStatistics,
  getModelInfo,
  trainModel,
  testConnection,
  startPolling,
  generateDemoTransaction,
  generateDemoTransactions
} = apiService;

// Export error class
export { ApiError };

// Default export
export default apiService;
