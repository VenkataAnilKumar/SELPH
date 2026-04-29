# Phase 0: Comprehensive Test Suite

## Overview

This document outlines the complete test suite for Phase 0, covering:
- Backend API (FastAPI)
- Web Frontend (Next.js + React)
- Mobile Frontend (React Native + Expo)

## Testing Strategy

### 1. Backend Testing

#### Unit Tests (`src/backend/tests/test_services.py`)
Test individual service methods in isolation with mocked dependencies.

**Coverage:**
- AuthService: signup, login, token generation
- TwinService: get, pause, resume, update
- MessageService: create, retrieve, mark processed
- DraftService: create, approve, reject, edit
- ModerationService: content safety, confidence scoring

**Execution:**
```bash
cd src/backend
pytest tests/test_services.py -v --tb=short
```

#### Integration Tests (`src/backend/tests/test_endpoints.py`)
Test API endpoints with actual database and dependencies.

**Coverage:**
- Auth endpoints: signup, login, logout, refresh, get current user
- Twin endpoints: get, pause, resume, update, stats
- Message endpoints: list, filter, pagination
- Draft endpoints: list pending, approve, reject, edit
- Health check endpoint

**Execution:**
```bash
cd src/backend
pytest tests/test_endpoints.py -v --tb=short
```

#### Acceptance Tests (`src/backend/tests/test_acceptance.py`)
Test complete user flows and Phase 0 requirements.

**Coverage:**
- User signup to dashboard flow
- User login flow
- Twin configuration flow
- Message receipt and processing
- Draft lifecycle (generate, approve, reject, edit)
- Twin pause/resume
- Authentication and authorization
- Data isolation between users
- Error handling
- Complete user journey

**Execution:**
```bash
cd src/backend
pytest tests/test_acceptance.py -v --tb=short
```

### 2. Web Frontend Testing

#### Component Tests (`src/web/tests/components.test.tsx`)
Test React components with React Testing Library.

**Coverage:**
- Auth storage (localStorage operations)
- Auth context (state management)
- Login form (validation, submission, errors)
- Signup form (password requirements, validation)
- Dashboard (twin profile, quick actions)
- Protected routes
- Form utilities (InputField, SubmitButton, alerts)

**Execution:**
```bash
cd src/web
npm test -- components.test.tsx
```

**Installation:**
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest @babel/preset-react ts-jest
```

### 3. Mobile Frontend Testing

#### Component Tests (`src/mobile/tests/components.test.tsx`)
Test React Native components with React Native Testing Library.

**Coverage:**
- Auth storage (SecureStore operations)
- Auth context (state management)
- Login screen (validation, submission, errors)
- Signup screen (password requirements, validation)
- Dashboard (twin profile, quick actions)
- Root layout (navigation control)
- Auth/Dashboard group layouts

**Execution:**
```bash
cd src/mobile
npm test -- components.test.tsx
```

**Installation:**
```bash
npm install --save-dev @testing-library/react-native jest
```

## Test Configuration

### Backend (`src/backend/pytest.ini`)
- Test discovery pattern: `test_*.py`
- Markers: unit, integration, acceptance, slow, auth, message, draft, twin
- Coverage reporting enabled

### Web (`src/web/jest.config.js` + `src/web/jest.setup.js`)
- Test environment: jsdom (browser-like)
- Module mapping for TypeScript imports
- localStorage mock
- matchMedia mock for responsive tests
- Coverage threshold: 50% globally

### Mobile (`src/mobile/jest.config.js` + `src/mobile/jest.setup.js`)
- Test environment: Node.js
- Expo Router mock
- SecureStore mock
- AsyncStorage mock
- Alert mock
- Coverage threshold: 40% globally (more lenient for native)

## Running Tests

### Backend Tests

```bash
# All tests
cd src/backend
pytest tests/ -v

# Unit tests only
pytest tests/test_services.py -v

# Integration tests only
pytest tests/test_endpoints.py -v

# Acceptance tests only
pytest tests/test_acceptance.py -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=html

# Run specific test
pytest tests/test_services.py::TestAuthService::test_signup_creates_user -v

# Run by marker
pytest tests/ -v -m acceptance
pytest tests/ -v -m "not slow"
```

### Web Tests

```bash
# All tests
cd src/web
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific test file
npm test -- components.test.tsx
```

### Mobile Tests

```bash
# All tests
cd src/mobile
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific test file
npm test -- components.test.tsx
```

### Full CI/CD Pipeline

```bash
# Run all tests (backend + web + mobile)
npm run test:all

# Run with coverage
npm run test:coverage
```

## Test Fixtures and Mocks

### Backend Fixtures (`conftest.py`)

```python
@pytest.fixture
def test_db():
    """In-memory SQLite database for tests"""

@pytest.fixture
def client():
    """FastAPI TestClient"""

@pytest.fixture
def test_user_data():
    """Sample user credentials"""

@pytest.fixture
def test_user(test_db):
    """Pre-created test user"""

@pytest.fixture
def auth_headers():
    """Authorization headers with valid JWT"""

@pytest.fixture
def test_message_data():
    """Sample message data"""

@pytest.fixture
def test_twin_data():
    """Sample twin configuration"""
```

### Web/Mobile Mocks

- API client mocked for all HTTP calls
- Router mocked for navigation
- localStorage/SecureStore mocked
- Timer mocks for async operations

## Expected Test Results

### Backend
- **Unit Tests**: 40+ tests covering all services
- **Integration Tests**: 20+ tests covering all endpoints
- **Acceptance Tests**: 10 user flow scenarios
- **Total**: 70+ tests
- **Expected Pass Rate**: 100%
- **Coverage Target**: >80% code coverage

### Web
- **Component Tests**: 30+ tests
- **Coverage Target**: 50%+ (may vary by complexity)

### Mobile
- **Component Tests**: 40+ tests
- **Coverage Target**: 40%+ (accounting for native complexity)

## Test Data

### Sample User
```python
{
    "email": "test@example.com",
    "password": "TestPassword123"  # 8+ chars, upper, lower, number
}
```

### Sample Twin Configuration
```python
{
    "domain": "business",
    "tone": "professional",
    "vocab": "formal",
    "avg_response_length": "medium"
}
```

### Sample Message
```python
{
    "channel": "instagram_dm",
    "sender_id": "user_123",
    "sender_name": "John Doe",
    "content": "Hey, how are you?",
    "channel_metadata": {"conversation_id": "conv_123"}
}
```

## Acceptance Criteria Testing

### Phase 0 Requirements Verification

1. ✅ **User Authentication**
   - Signup with email/password
   - Login with credentials
   - Logout clears session
   - Protected routes require auth

2. ✅ **Twin Management**
   - Auto-created on signup
   - Configurable personality
   - Pauseable/resumable
   - Statistics tracking

3. ✅ **Message Handling**
   - Receive from channels
   - Store in database
   - Track status (received, processed, draft_ready)
   - Query by filters

4. ✅ **Draft Generation**
   - Create drafts from messages
   - User review/approval
   - Rejection/editing
   - Status tracking (pending, approved, rejected)

5. ✅ **Data Isolation**
   - Users only see their data
   - Secure authorization checks
   - Database foreign keys enforce integrity

6. ✅ **Error Handling**
   - Graceful error responses
   - User-friendly messages
   - Proper HTTP status codes
   - Validation errors reported

## Test Execution Timeline

### Phase 0 Testing Schedule
1. **Week 1**: Backend unit tests (services)
2. **Week 2**: Backend integration tests (endpoints)
3. **Week 3**: Backend acceptance tests (user flows)
4. **Week 4**: Web component tests
5. **Week 5**: Mobile component tests
6. **Week 6**: Full test suite validation + CI/CD integration

## Continuous Integration

GitHub Actions workflows automatically run:
- Backend tests on PR (pytest)
- Web tests on PR (Jest)
- Mobile tests on PR (Jest)
- Coverage reports generated
- Failed tests block merge to main

## Troubleshooting

### Backend Issues

**`ModuleNotFoundError: No module named 'app'`**
```bash
# Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src/backend"
pytest tests/
```

**`Database connection error`**
```bash
# Tests use in-memory SQLite, should work offline
# Verify conftest.py fixtures are correct
```

### Web/Mobile Issues

**`Cannot find module`**
```bash
# Install dependencies
npm install
# Verify tsconfig paths
```

**`Mock not working`**
```bash
# Ensure jest.setup.js is referenced in jest.config.js
# Clear Jest cache: npm test -- --clearCache
```

## Next Steps

1. Run full test suite locally
2. Verify 100% pass rate
3. Check coverage metrics
4. Integrate with GitHub Actions
5. Set up branch protection requiring passing tests
6. Document test results in PRs
7. Maintain/update tests for Phase 1+ features

## References

- pytest docs: https://docs.pytest.org/
- React Testing Library: https://testing-library.com/react
- React Native Testing Library: https://callstack.github.io/react-native-testing-library/
- Jest docs: https://jestjs.io/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
