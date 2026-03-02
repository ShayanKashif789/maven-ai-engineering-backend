# Global Constraint Framework

This document defines the universal constraints that apply to ALL features, components, and assignments within the system. These constraints are enforceable, testable, and must be followed by all contributors (human or AI).

---

## 1. Functional Constraints (Global Rules)

### Input/Output Standards
- **MUST**: All API endpoints accept and return JSON-formatted data
- **MUST**: All public functions have type hints for parameters and return values
- **MUST**: All user-facing text be in English unless explicitly specified otherwise
- **MUST NOT**: Functions return `None` for error cases - use proper error handling
- **MUST**: All string inputs be stripped of leading/trailing whitespace before processing

### Behavior Requirements
- **MUST**: All operations be idempotent where safe and appropriate
- **MUST**: All state modifications be atomic within a single request/response cycle
- **MUST**: All external API calls have timeout protection (maximum 30 seconds)
- **MUST NOT**: Operations block indefinitely without timeout or cancellation mechanism
- **MUST**: All file operations use absolute paths, never relative paths

### Data Processing Rules
- **MUST**: All text processing handle Unicode characters correctly
- **MUST**: All numeric inputs be validated for type and range before use
- **MUST**: All date/time operations use UTC timezone unless explicitly specified
- **MUST NOT**: Sensitive data be logged or included in error messages

---

## 2. Architectural Constraints

### System Integration
- **MUST**: New features integrate through existing API routers, not create new FastAPI instances
- **MUST**: All new modules be placed under appropriate assignment directories
- **MUST NOT**: Modify core system files (`main.py`, `config.py`) without architectural review
- **MUST**: All new endpoints follow the `/api/{assignment}` prefix pattern

### Component Modification Rules
- **MUST NOT**: Modify existing agent signatures without updating all dependent components
- **MUST**: All changes to shared utilities maintain backward compatibility
- **MUST**: New dependencies be added to `requirements.txt` with version pinning
- **MUST NOT**: Import modules from sibling assignments directly - use proper abstractions

### Reusability Requirements
- **MUST**: All utility functions be placed in shared modules when used by multiple assignments
- **MUST**: All configuration values be externalized to `config.py` or environment variables
- **MUST**: All database operations use the established connection patterns
- **MUST**: Error handling follow the established patterns in each assignment

---

## 3. Agent Responsibility Constraints

### Separation of Responsibilities
- **MUST**: Each agent have a single, well-defined responsibility
- **MUST NOT**: Agents directly call other agents - use the orchestrator pattern
- **MUST**: Agent logic be contained within its designated module
- **MUST NOT**: Agents modify state outside their designated responsibility areas

### Communication Boundaries
- **MUST**: All agent communication occur through the shared state object
- **MUST**: Agents read from state but only modify their designated fields
- **MUST NOT**: Agents maintain hidden state or global variables
- **MUST**: All agent inputs/outputs be documented in the state schema

### Logic Overlap Prevention
- **MUST**: Classification logic be centralized in supervisor agents
- **MUST**: Data transformation logic be isolated to specific agents
- **MUST NOT**: Multiple agents perform the same validation checks
- **MUST**: Business logic be separated from infrastructure concerns

---

## 4. Data & Schema Constraints

### Standard Formats
- **MUST**: All API request/response models use Pydantic for validation
- **MUST**: All configuration use environment variables with proper defaults
- **MUST**: All datetime objects use ISO 8601 format in JSON
- **MUST**: All file paths use forward slashes, even on Windows

### Validation Requirements
- **MUST**: All user inputs be validated before processing
- **MUST**: All external API responses be validated before use
- **MUST**: All file uploads have size and type validation
- **MUST NOT**: Trust data from external sources without validation

### Data Consistency Rules
- **MUST**: All database operations use transactions for multi-step operations
- **MUST**: All cache invalidation be consistent across the system
- **MUST**: All state transitions be valid according to state machine definitions
- **MUST NOT**: Allow partial state updates that break invariants

---

## 5. Performance Constraints

### Latency Requirements
- **MUST**: All API endpoints respond within 60 seconds for normal operations
- **MUST**: All database queries have appropriate indexes and execute within 5 seconds
- **MUST**: All file operations complete within 10 seconds for files under 10MB
- **MUST NOT**: Perform synchronous I/O operations in request handlers for large operations

### Resource Usage Limits
- **MUST**: All processes limit memory usage to 2GB per request
- **MUST**: All concurrent operations be limited to prevent resource exhaustion
- **MUST**: All temporary files be cleaned up after processing
- **MUST NOT**: Load entire large files into memory - use streaming

### Scalability Requirements
- **MUST**: All designs support horizontal scaling where applicable
- **MUST**: All stateless components be easily replicable
- **MUST**: All database connections use connection pooling
- **MUST NOT**: Use in-memory storage for persistent data

---

## 6. Security Constraints

### Data Protection
- **MUST**: All sensitive data be encrypted at rest
- **MUST**: All API communications use HTTPS in production
- **MUST**: All user passwords be hashed using bcrypt or better
- **MUST NOT**: Store API keys or secrets in code or configuration files

### Input Validation
- **MUST**: All user inputs be sanitized to prevent injection attacks
- **MUST**: All file uploads be scanned for malicious content
- **MUST**: All SQL queries use parameterized statements
- **MUST NOT**: Execute user-provided code or commands

### Access Control
- **MUST**: All API endpoints have appropriate authentication and authorization
- **MUST**: All administrative operations require elevated privileges
- **MUST**: All rate limiting be implemented to prevent abuse
- **MUST NOT**: Expose internal system information in error messages

---

## 7. Testing Constraints

### Coverage Requirements
- **MUST**: All new code have minimum 80% test coverage
- **MUST**: All critical paths have 100% test coverage
- **MUST**: All API endpoints have integration tests
- **MUST NOT**: Merge code without passing all tests

### Test Types Required
- **MUST**: Unit tests for all business logic
- **MUST**: Integration tests for all external dependencies
- **MUST**: End-to-end tests for all user workflows
- **MUST**: Performance tests for all critical paths

### Test Quality Standards
- **MUST**: All tests be deterministic and repeatable
- **MUST**: All tests use test data, not production data
- **MUST**: All error conditions be tested
- **MUST NOT**: Use sleep() or other timing-dependent assertions

---

## 8. Logging & Observability Constraints

### Logging Requirements
- **MUST**: All significant operations be logged with appropriate levels
- **MUST**: All errors be logged with full context and stack traces
- **MUST**: All logs use structured format (JSON) for machine parsing
- **MUST NOT**: Log sensitive information or PII

### Traceability Rules
- **MUST**: All requests have unique correlation IDs
- **MUST**: All log entries include correlation IDs for request tracing
- **MUST**: All external API calls be logged with request/response details
- **MUST**: All performance metrics be collected and reported

### Debugging Support
- **MUST**: All components support debug mode with enhanced logging
- **MUST**: All configuration values be loggable at startup
- **MUST**: All state transitions be traceable through logs
- **MUST NOT**: Expose internal implementation details in production logs

---

## 9. Failure Handling Constraints

### Retry Policies
- **MUST**: All external API calls implement exponential backoff retry
- **MUST**: All retry attempts be limited to maximum 3 attempts
- **MUST**: All retry logic be circuit-breaker aware
- **MUST NOT**: Retry indefinitely or without proper limits

### Fallback Mechanisms
- **MUST**: All critical operations have defined fallback behavior
- **MUST**: All fallback responses be clearly marked as degraded
- **MUST**: All fallback modes preserve system stability
- **MUST NOT**: Return empty or null responses without clear indication

### Error Standardization
- **MUST**: All errors use consistent error response format
- **MUST**: All error messages be user-friendly and actionable
- **MUST**: All errors be categorized and logged appropriately
- **MUST NOT**: Expose internal system details in error responses

---

## 10. Extensibility Constraints

### Future Scalability Design
- **MUST**: All new features be designed for horizontal scaling
- **MUST**: All interfaces be versioned for backward compatibility
- **MUST**: All configurations be externalizable for different environments
- **MUST NOT**: Create tight coupling between components

### Modularity Requirements
- **MUST**: All features be implemented as independent modules
- **MUST**: All dependencies be injected rather than hardcoded
- **MUST**: All interfaces be abstracted for easy replacement
- **MUST NOT**: Create circular dependencies between modules

### Adaptability Rules
- **MUST**: All business logic be separated from infrastructure code
- **MUST**: All data access be abstracted through repository patterns
- **MUST**: All external integrations be adapter-based
- **MUST NOT**: Hardcode business rules that may change frequently

---

## Enforcement Mechanisms

### Automated Checks
- **MUST**: CI/CD pipeline validates all constraints automatically
- **MUST**: Pre-commit hooks enforce code style and basic rules
- **MUST**: Static analysis tools verify architectural constraints
- **MUST**: Security scans validate security constraints

### Review Process
- **MUST**: All code changes require peer review
- **MUST**: All architectural changes require design review
- **MUST**: All new features require constraint compliance check
- **MUST NOT**: Bypass constraint enforcement without explicit approval

### Monitoring
- **MUST**: Constraint violations be monitored and alerted
- **MUST**: Performance constraints be continuously monitored
- **MUST**: Security constraints be regularly audited
- **MUST**: All constraint metrics be tracked over time

---

## Constraint Violation Handling

### Violation Classification
- **Critical**: Security breaches, data corruption, system downtime
- **High**: Performance degradation, reliability issues
- **Medium**: Code quality, maintainability issues
- **Low**: Style, documentation, minor improvements

### Resolution Requirements
- **Critical**: Must be resolved immediately before deployment
- **High**: Must be resolved within 24 hours
- **Medium**: Must be resolved within 1 week
- **Low**: Should be resolved in next development cycle

### Prevention Measures
- **MUST**: Root cause analysis for all violations
- **MUST**: Process updates to prevent recurrence
- **MUST**: Team training on constraint requirements
- **MUST**: Regular constraint compliance audits
