# Create Go Structs from API Documentation

Generate idiomatic Go structs from API documentation with proper types, tags, and validation.

## Overview

This command extracts API endpoint documentation and generates corresponding Go structs for requests and responses. It handles complex nested structures, nullable fields, enums, and follows Go best practices.

## Phase 1: Documentation Extraction

### Extract API Documentation using mcp tool:
```
get_docs($ARGUMENTS[0], $ARGUMENTS[1])
```

**Parameters:**
- `$ARGUMENTS[0]`: URL of the API documentation page
- `$ARGUMENTS[1]`: Specific endpoint or section to extract (e.g., "GET /accounts endpoint with full request and response")

### Extraction Guidelines

1. **Target Information:**
   - HTTP method and endpoint path
   - Request json structure (if applicable)
   - Response json structure (success and error cases)
   - Query parameters and path parameters
   - Headers requirements
   - Field descriptions and constraints

2. **Multiple Endpoints:**
   - If documentation contains multiple endpoints, extract all related ones
   - Group by resource type (e.g., all account-related endpoints together)

3. **Fallback Strategy:**
   - If specific extraction fails, try broader extraction
   - Look for JSON examples in code blocks
   - Extract from tables or structured documentation

### Example Phase 1 Usage
```
get_docs("https://developer.tastytrade.com/api-guides/customer-account-info", 
         "json for the GET /customers/me/accounts")
```

### Example response  and output from the `get_docs` tool usage:
```json
The JSON response for GET /customers/me/accounts:

{
    "data": {
        "items": [
            {
                "account": {
                    "account-number": "5WT00001",
                    "external-id": "A0000196557",
                    "opened-at": "2019-03-14T15:39:31.265+00:00",
                    "nickname": "Individual",
                    "account-type-name": "Individual",
                    "day-trader-status": false,
                    "is-closed": false,
                    "is-firm-error": false,
                    "is-firm-proprietary": false,
                    "is-futures-approved": true,
                    "is-test-drive": false,
                    "margin-or-cash": "Margin",
                    "is-foreign": false,
                    "funding-date": "2017-01-02",
                    "investment-objective": "SPECULATION",
                    "futures-account-purpose": "SPECULATING",
                    "suitable-options-level": "No Restrictions",
                    "created-at": "2019-03-14T15:39:31.265+00:00"
                },
                "authority-level": "owner"
            }
        ]
    }
}
```

## Phase 2: Go Struct Generation

### Struct Generation Rules

1. **Type Mapping:**
   - `string` → `string`
   - `number/float` → `float64` (or `float32` if specified)
   - `integer` → `int64` (or `int32/int` if specified)
   - `boolean` → `bool`
   - `array` → `[]Type`
   - `object` → Custom struct or `map[string]interface{}` for dynamic objects
   - `null` or nullable → Use pointer types (`*Type`)
   - ISO 8601 dates → `time.Time`
   - Timestamps → `time.Time` or `int64` (Unix timestamps)

2. **Naming Conventions:**
   - Use PascalCase for exported struct names
   - Use PascalCase for exported field names
   - Prefix unexported types with lowercase
   - Use descriptive names (e.g., `CustomerAccount` not just `Account`)

3. **JSON Tags:**
   ```go
   type CustomerAccount struct {
       ID          string     `json:"id"`
       CustomerID  string     `json:"customer_id"`
       AccountNum  string     `json:"account_number"`
       CreatedAt   time.Time  `json:"created_at"`
       Balance     *float64   `json:"balance,omitempty"`
       IsActive    bool       `json:"is_active"`
   }
   ```

4. **Validation Tags (if using validator/v10):**
   ```go
   type CreateAccountRequest struct {
       CustomerID  string  `json:"customer_id" validate:"required,uuid"`
       AccountType string  `json:"account_type" validate:"required,oneof=checking savings"`
       InitialDep  float64 `json:"initial_deposit" validate:"min=0"`
   }
   ```

5. **Enum Handling:**
   ```go
   // AccountStatus represents the status of an account
   type AccountStatus string
   
   const (
       AccountStatusActive   AccountStatus = "ACTIVE"
       AccountStatusInactive AccountStatus = "INACTIVE"
       AccountStatusPending  AccountStatus = "PENDING"
   )
   ```

6. **Error Response Structures:**
   ```go
   type ErrorResponse struct {
       Error   string            `json:"error"`
       Code    string            `json:"code"`
       Message string            `json:"message"`
       Details map[string]string `json:"details,omitempty"`
   }
   ```

### Output Structure

1. **Package Declaration:**
   ```go
   package models // or api, types, etc.
   ```

2. **Imports:**
   ```go
   import (
       "time"
       "encoding/json"
   )
   ```

3. **Type Definitions:**
   - Group related structs together
   - Place request structs before response structs
   - Include pagination structs if applicable

4. **Helper Methods (when appropriate):**
   ```go
   // Validate performs validation on the request
   func (r *CreateAccountRequest) Validate() error {
       // Custom validation logic
   }
   ```

### Complex Structure Examples

1. **Nested Objects:**
   ```go
   type AccountResponse struct {
       Account  Account   `json:"account"`
       Customer Customer  `json:"customer"`
       Metadata Metadata  `json:"metadata"`
   }
   ```

2. **Pagination:**
   ```go
   type PaginatedResponse struct {
       Data       []Account   `json:"data"`
       Pagination Pagination  `json:"pagination"`
   }
   
   type Pagination struct {
       Page       int  `json:"page"`
       PerPage    int  `json:"per_page"`
       Total      int  `json:"total"`
       TotalPages int  `json:"total_pages"`
   }
   ```

3. **Generic Responses:**
   ```go
   type APIResponse[T any] struct {
       Success bool   `json:"success"`
       Data    T      `json:"data,omitempty"`
       Error   *Error `json:"error,omitempty"`
   }
   ```

### Special Considerations

1. **Nullable Fields:**
   - Use pointers for fields that can be null
   - Add `omitempty` tag for optional fields

2. **Custom Unmarshalers:**
   - Generate for complex date formats
   - Handle string-encoded numbers or booleans

3. **Documentation:**
   - Add struct-level comments describing the purpose
   - Add field-level comments for non-obvious fields
   - Include example usage in comments

4. **Testing Helpers:**
   - Consider generating factory functions
   - Include JSON marshaling/unmarshaling tests

## Notes

- Always check generated structs against actual API responses
- Adjust field types based on your specific use case
- Consider using code generation tools for large APIs
- Validate against API contracts/OpenAPI specs when available
