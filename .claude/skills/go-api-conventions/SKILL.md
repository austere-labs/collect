# Go Fasthttp Endpoint Builder

Create new API endpoints following the project conventions using fasthttp.

## File Structure

- Handlers go in `internal/api/{domain}Handlers.go` (e.g., `userHandlers.go`, `aiHandlers.go`)
- Tests go in `internal/api/{domain}Handlers_test.go`
- Request/response types go in `internal/models/handlersJSON.go`
- URL constants go in `internal/api/urls.go`
- Error helpers go in `internal/api/errors.go`
- Routes are registered in `internal/api/router.go`
- `encode` and `decode` generic helpers live in `internal/api/application.go`

## Handler Signature

All handlers are receiver methods on `*Application`:

```go
func (app *Application) HandlerName(ctx *fasthttp.RequestCtx) {
    // handler logic
}
```

## Request Parsing

Use the generic `decode[T]` helper to parse JSON request bodies:

```go
requestData, decodeErr := decode[models.MyRequest](ctx)
if decodeErr != nil {
    app.requestParsingErr(ctx, decodeErr)
    return
}
```

Access path parameters with `ctx.UserValue("paramName")`.

## Response Writing

Use the generic `encode[T]` helper. It sets `Content-Type: application/json`, optionally sets a cookie, sets the status code, and JSON-encodes the response:

```go
encode(ctx, fasthttp.StatusOK, nil, responseData)        // no cookie
encode(ctx, fasthttp.StatusCreated, cookie, responseData) // with cookie
```

## Error Handling

Use the named error helpers from `errors.go`. Each logs the error with zerolog and writes a JSON `APIError` response:

```go
app.requestParsingErr(ctx, err)      // 400 - malformed request body
app.badRequestErr(ctx, err)          // 400 - validation failure
app.unauthorized(ctx, err)           // 401 - auth failure
app.retrievingUserErr(ctx, err)      // 500 - database read failure
app.internalDatabaseErr(ctx, err)    // 500 - database write failure
app.internalServerErr(ctx, err)      // 500 - generic server error
app.cookieUpdateErr(ctx, err)        // 500 - cookie/JWT failure
app.userAlreadyExists(ctx, err)      // 500 - duplicate user
app.expiredResetRequestErr(ctx, err) // 500 - expired reset token
```

If a new domain-specific error is needed, add it to `errors.go` following this pattern:

```go
func (app *Application) myNewErr(ctx *fasthttp.RequestCtx, err error) {
    desc := "description of what went wrong"
    solution := "suggestion for the caller"
    app.logger.Err(err).Msg(desc)
    writeError(ctx, fasthttp.StatusBadRequest, desc, solution)
}
```

## Request/Response Types

Define in `internal/models/handlersJSON.go` with JSON tags:

```go
type MyRequest struct {
    FieldOne string `json:"fieldOne"`
    FieldTwo int    `json:"fieldTwo"`
}

type MyResponse struct {
    ID     string `json:"id"`
    Status string `json:"status"`
}
```

## URL Constants

Add to `internal/api/urls.go`:

```go
const MyNewEndpointURL = "/api/v1/my-resource"
```

## Route Registration

Add to `BuildRoutes()` in `internal/api/router.go`:

```go
// Public route
r.POST(MyNewEndpointURL, app.MyHandler)

// Authenticated route (requires JWT cookie)
r.PUT(MyNewEndpointURL, app.auth(app.MyHandler))
```

## Complete Handler Template

```go
func (app *Application) CreateWidget(ctx *fasthttp.RequestCtx) {
    app.logger.Info().Msg("creating widget")

    // 1. Parse request
    widgetReq, decodeErr := decode[models.CreateWidgetRequest](ctx)
    if decodeErr != nil {
        app.requestParsingErr(ctx, decodeErr)
        return
    }

    // 2. Business logic / validation
    if widgetReq.Name == "" {
        app.badRequestErr(ctx, errors.New("widget name is required"))
        return
    }

    // 3. Database interaction
    widget := models.Widget{
        WidgetID: uuid.New().String(),
        Name:     widgetReq.Name,
    }

    _, createErr := app.widgetRepo.CreateWidget(widget)
    if createErr != nil {
        app.internalDatabaseErr(ctx, createErr)
        return
    }

    // 4. Return response
    response := models.CreateWidgetResponse{
        ID:   widget.WidgetID,
        Name: widget.Name,
    }

    encode(ctx, fasthttp.StatusCreated, nil, response)
}
```

## Testing Pattern

Tests use real dependencies (NO MOCKS) and `assert.Serve` for in-memory HTTP testing.

### Test Setup

Tests use `TestMain` for shared setup/teardown. The test file creates a real `*Application` with real database, config, and dependencies:

```go
var app *Application

func TestMain(m *testing.M) {
    flag.Parse()
    setup()
    code := m.Run()
    shutdown()
    os.Exit(code)
}
```

### Basic Test

```go
func TestCreateWidget(t *testing.T) {
    widgetReq := models.CreateWidgetRequest{
        Name: "test widget",
    }

    url := "http://localhost:80" + CreateWidgetURL
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    req.SetRequestURI(url)
    req.Header.SetMethod("POST")
    json.NewEncoder(req.BodyWriter()).Encode(widgetReq)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    err := assert.Serve(app.BuildRoutes(), req, resp)
    if err != nil {
        t.Errorf("error serving request: %v", err)
    }

    assert.Equal(t, fasthttp.StatusCreated, resp.StatusCode())

    var response models.CreateWidgetResponse
    json.NewDecoder(bytes.NewReader(resp.Body())).Decode(&response)

    assert.Equal(t, "test widget", response.Name)
}
```

### Authenticated Endpoint Test

First call signup to get a JWT cookie, then extract and attach it:

```go
// 1. Sign up to get a JWT cookie
signupReq := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(signupReq)
signupReq.SetRequestURI("http://localhost:80" + SignupURL)
signupReq.Header.SetMethod("POST")
json.NewEncoder(signupReq.BodyWriter()).Encode(models.UserSignup{
    Email: "test@test.com", Password: "password",
})

signupRes := fasthttp.AcquireResponse()
defer fasthttp.ReleaseResponse(signupRes)
assert.Serve(app.BuildRoutes(), signupReq, signupRes)

// 2. Extract JWT cookie value
var jwtCookie string
signupRes.Header.VisitAllCookie(func(key, value []byte) {
    if string(key) == "jwt" {
        jwtCookie = string(value)
    }
})
jwtCookie = jwtCookie[4:] // strip "jwt=" prefix

// 3. Attach cookie to authenticated request
req.Header.SetCookie("jwt", jwtCookie)
```

### Available Assert Helpers

From `pkg/assert`:
- `assert.Equal(t, expected, actual)` - generic comparable equality
- `assert.NotEqual(t, expected, actual)` - generic comparable inequality
- `assert.NotNil(t, actual)` - nil check
- `assert.Nil(t, actual)` - nil check
- `assert.DeepEqual(t, expected, actual)` - reflect.DeepEqual
- `assert.ErrorContains(err, "substring")` - error message check
- `assert.Between(t, min, max, actual)` - range check
- `assert.Serve(handler, req, resp)` - in-memory fasthttp request

## Middleware

To protect a route with authentication, wrap with `app.auth()`:

```go
r.PUT(MyEndpointURL, app.auth(app.MyHandler))
```

The auth middleware extracts `userEmail` and `userId` from the JWT and sets them on the context:

```go
userEmail := ctx.UserValue("userEmail").(string)
userId := ctx.UserValue("userId").(string)
```

## Key Libraries

- Router: `github.com/fasthttp/router`
- HTTP: `github.com/valyala/fasthttp`
- Logging: `github.com/rs/zerolog`
- UUIDs: `github.com/google/uuid`
- Database: SQLite3 (`github.com/mattn/go-sqlite3`)
- Migrations: `github.com/golang-migrate/migrate/v4`
- Assertions: `elephnt/pkg/assert` (custom package)
- Metrics: `github.com/prometheus/client_golang`

## Checklist for New Endpoints

1. [ ] Define request/response structs in `internal/models/handlersJSON.go`
2. [ ] Add URL constant in `internal/api/urls.go`
3. [ ] Write handler method in `internal/api/{domain}Handlers.go`
4. [ ] Register route in `internal/api/router.go` (with `app.auth()` if protected)
5. [ ] Add any new error helpers in `internal/api/errors.go` if needed
6. [ ] Write tests in `internal/api/{domain}Handlers_test.go`
7. [ ] Add any new repository methods if database access is needed
