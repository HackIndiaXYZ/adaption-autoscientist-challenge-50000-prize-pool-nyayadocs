# Tests

## Running Tests

Install test dependencies:
```bash
pip install -r requirements.txt
```

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_intent.py -v
```

## Test Coverage

- `test_intent.py` - Intent classification and entity extraction tests
  - Bail application intent detection
  - Surety bond intent detection
  - Case status intent detection
  - Legal aid intent detection
  - Rule-based extraction with entities
  - Multilingual intent classification
  - Intent keyword matching

## Adding New Tests

Follow the existing pattern:
1. Import necessary modules from `main.py`
2. Create test class with descriptive name
3. Add test methods with clear assertions
4. Run tests to verify
