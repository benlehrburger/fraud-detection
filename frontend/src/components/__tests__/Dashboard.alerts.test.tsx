import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Dashboard } from '../Dashboard';
import { Alert, Statistics } from '../../services/api';

const mockStatistics: Statistics = {
  total_transactions: 1000,
  fraud_rate: 2.5,
  risk_distribution: { LOW: 800, MEDIUM: 150, HIGH: 50 },
  alerts_count: 10,
  model_status: 'trained'
};


const createMockAlert = (severity: Alert['severity'], id: string = '1'): Alert => ({
  id,
  transaction_id: 'TXN_001',
  severity,
  risk_score: 0.8,
  action_required: 'INVESTIGATE',
  reason: 'Suspicious transaction pattern detected',
  merchant: 'Test Merchant',
  amount: 500,
  location: 'New York, NY',
  created_at: '2023-12-01T10:00:00Z',
  status: 'OPEN'
});

describe('Dashboard Alert System', () => {
  test('renders alerts section when alerts are present', () => {
    const alerts = [createMockAlert('HIGH')];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('Recent Alerts')).toBeInTheDocument();
    expect(screen.getByText('1 active')).toBeInTheDocument();
  });

  test('does not render alerts section when no alerts present', () => {
    render(
      <Dashboard
        transactions={[]}
        alerts={[]}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.queryByText('Recent Alerts')).not.toBeInTheDocument();
  });

  test('displays correct alert count in active alerts indicator', () => {
    const alerts = [
      createMockAlert('HIGH', '1'),
      createMockAlert('MEDIUM', '2'),
      createMockAlert('CRITICAL', '3')
    ];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('3 active')).toBeInTheDocument();
  });

  test('shows correct critical and high alert counts in metrics', () => {
    const alerts = [
      createMockAlert('CRITICAL', '1'),
      createMockAlert('CRITICAL', '2'),
      createMockAlert('HIGH', '3'),
      createMockAlert('MEDIUM', '4')
    ];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('2 critical, 1 high')).toBeInTheDocument();
  });

  test('displays alert severity correctly', () => {
    const alerts = [createMockAlert('HIGH')];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  test('displays alert amount with proper formatting', () => {
    const alerts = [createMockAlert('HIGH')];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('$500')).toBeInTheDocument();
  });

  test('shows only first 5 alerts when more than 5 are present', () => {
    const alerts = Array.from({ length: 8 }, (_, i) =>
      createMockAlert('HIGH', `alert_${i + 1}`)
    );

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    // Should show "8 active" but only render 5 alert items
    expect(screen.getByText('8 active')).toBeInTheDocument();

    // Count alert items (each has severity badge)
    const alertItems = screen.getAllByText('HIGH');
    expect(alertItems).toHaveLength(5);
  });

  test('displays correct alert action buttons', () => {
    const alerts = [createMockAlert('HIGH')];

    render(
      <Dashboard
        transactions={[]}
        alerts={alerts}
        statistics={mockStatistics}
        loading={false}
        onRefresh={() => {}}
      />
    );

    // Check for the correct button text
    expect(screen.getByText('Investigate')).toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
  });
});