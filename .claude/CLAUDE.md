# FinTechCo Development Standards

## Security Requirements
- All financial calculations MUST use Decimal type, never float
- Input validation required for ALL user inputs
- PCI DSS compliance is mandatory
- Implement rate limiting on all API endpoints
- Log all transactions with correlation IDs

## Code Standards
- Python: Follow PEP 8, use type hints
- TypeScript: Strict mode enabled, no any types
- All database queries must use parameterized statements
- Sensitive data must be encrypted at rest and in transit

## Testing Requirements
- Minimum 80% code coverage
- Security tests for all endpoints
- Performance tests for high-volume operations

## Compliance
- GDPR compliance for EU customers
- SOC 2 Type II requirements
- Regular security audits required