# Data Normalization Guide

How to use URWA's data normalization features.

---

## Overview

Raw scraped data is messy. Normalization converts it to consistent, structured formats.

Example:
```
Input:  "$1,234.56 USD"
Output: {"amount": 1234.56, "currency": "USD"}
```

---

## API Endpoint

```bash
POST /api/v1/normalize?data_type={type}&value={raw_value}
```

---

## Price Normalization

Converts price strings to structured format.

### Supported Formats

| Input | Output |
|-------|--------|
| "$1,234.56" | `{amount: 1234.56, currency: "USD"}` |
| "EUR 99.99" | `{amount: 99.99, currency: "EUR"}` |
| "1,000" | `{amount: 1000.0, currency: "USD"}` |
| "Rs. 5,999" | `{amount: 5999.0, currency: "INR"}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=price&value=\$1,234.56"
```

Response:
```json
{
  "status": "success",
  "input": "$1,234.56",
  "normalized": {
    "amount": 1234.56,
    "currency": "USD",
    "raw": "$1,234.56"
  }
}
```

### Currency Detection

| Symbol | Currency |
|--------|----------|
| $ | USD |
| EUR | EUR |
| GBP | GBP |
| JPY | JPY |
| INR | INR |
| A$ | AUD |
| C$ | CAD |

---

## Date Normalization

Converts date strings to ISO format.

### Supported Formats

| Input | Output |
|-------|--------|
| "2024-01-15" | `{iso: "2024-01-15"}` |
| "Jan 15, 2024" | `{iso: "2024-01-15"}` |
| "15/01/2024" | `{iso: "2024-01-15"}` |
| "January 15, 2024" | `{iso: "2024-01-15"}` |
| "15 Jan 2024" | `{iso: "2024-01-15"}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=date&value=Jan%2015,%202024"
```

Response:
```json
{
  "status": "success",
  "input": "Jan 15, 2024",
  "normalized": {
    "iso": "2024-01-15",
    "timestamp": 1705276800,
    "raw": "Jan 15, 2024"
  }
}
```

---

## Location Normalization

Parses location strings into components.

### Supported Formats

| Input | Output |
|-------|--------|
| "New York, NY, USA" | `{city, state, country}` |
| "London, UK" | `{city: "London", country: "UK"}` |
| "Remote" | `{remote: true}` |
| "San Francisco, CA" | `{city, state: "CA", country: "USA"}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=location&value=New%20York,%20NY"
```

Response:
```json
{
  "status": "success",
  "input": "New York, NY",
  "normalized": {
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "remote": false,
    "raw": "New York, NY"
  }
}
```

---

## Company Name Normalization

Cleans company names and extracts legal suffixes.

### Transformations

| Input | Output |
|-------|--------|
| "Google LLC" | `{name: "Google", suffix: "LLC"}` |
| "APPLE INC." | `{name: "Apple", suffix: "Inc"}` |
| "amazon.com" | `{name: "Amazon"}` |
| "Microsoft Corporation" | `{name: "Microsoft", suffix: "Corporation"}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=company&value=Google%20LLC"
```

Response:
```json
{
  "status": "success",
  "input": "Google LLC",
  "normalized": {
    "name": "Google",
    "legal_suffix": "LLC",
    "raw": "Google LLC"
  }
}
```

### Recognized Suffixes

LLC, Inc, Corp, Ltd, Limited, Co, Corporation, GmbH, S.A., PLC

---

## Rating Normalization

Standardizes rating formats.

### Supported Formats

| Input | Output |
|-------|--------|
| "4.5 out of 5" | `{value: 4.5, max: 5, percent: 90}` |
| "4.5/5" | `{value: 4.5, max: 5, percent: 90}` |
| "4.5 stars" | `{value: 4.5, max: 5, percent: 90}` |
| "90%" | `{value: 4.5, max: 5, percent: 90}` |
| "8/10" | `{value: 8, max: 10, percent: 80}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=rating&value=4.5%20out%20of%205"
```

Response:
```json
{
  "status": "success",
  "input": "4.5 out of 5",
  "normalized": {
    "value": 4.5,
    "max": 5.0,
    "percent": 90.0,
    "raw": "4.5 out of 5"
  }
}
```

---

## Phone Normalization

Converts phone numbers to E.164 format.

### Supported Formats

| Input | Output |
|-------|--------|
| "(555) 123-4567" | `{e164: "+15551234567"}` |
| "555-123-4567" | `{e164: "+15551234567"}` |
| "+1 555 123 4567" | `{e164: "+15551234567"}` |
| "5551234567" | `{e164: "+15551234567"}` |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=phone&value=(555)%20123-4567"
```

Response:
```json
{
  "status": "success",
  "input": "(555) 123-4567",
  "normalized": {
    "e164": "+15551234567",
    "raw": "(555) 123-4567"
  }
}
```

---

## Programmatic Usage

```python
from app.core.data_quality import data_normalizer

# Normalize a price
price = data_normalizer.normalize_price("$1,234.56")
print(price["amount"])  # 1234.56

# Normalize a date
date = data_normalizer.normalize_date("Jan 15, 2024")
print(date["iso"])  # "2024-01-15"

# Normalize a location
loc = data_normalizer.normalize_location("New York, NY")
print(loc["city"])  # "New York"
```

---

## Batch Normalization

For multiple values, call the API in a loop or use Python directly:

```python
from app.core.data_quality import data_normalizer

prices = ["$10.99", "$24.99", "$149.00"]
normalized_prices = [data_normalizer.normalize_price(p) for p in prices]
```

---

## Error Handling

When normalization fails, the raw value is preserved:

```json
{
  "status": "success",
  "input": "not a price",
  "normalized": {
    "amount": null,
    "currency": null,
    "raw": "not a price"
  }
}
```

Check for `null` values in output to detect parsing failures.

---

## Best Practices

1. Always preserve the `raw` value for debugging
2. Handle `null` amounts/values gracefully
3. Default to expected currency/format when ambiguous
4. Log parsing failures for improvement
5. Use batch processing for efficiency
