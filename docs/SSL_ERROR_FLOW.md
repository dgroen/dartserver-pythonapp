# SSL Error Handling Flow Diagram

## Overview

This document illustrates how SSL error handling works in the Darts Game Server.

---

## Normal HTTPS Request Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTPS Request
       │ (SSL Handshake)
       ▼
┌─────────────────────┐
│  Eventlet WSGI      │
│  SSL Layer          │
└──────┬──────────────┘
       │ SSL Handshake OK
       ▼
┌─────────────────────┐
│  Flask Application  │
│  (app.py)           │
└──────┬──────────────┘
       │ Process Request
       ▼
┌─────────────────────┐
│  HTTP Response      │
│  (200 OK)           │
└─────────────────────┘
```

**Result**: ✅ Request succeeds, response returned

---

## HTTP Request to HTTPS Server (Before Fix)

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP Request
       │ (No SSL Handshake)
       ▼
┌─────────────────────┐
│  Eventlet WSGI      │
│  SSL Layer          │
└──────┬──────────────┘
       │ SSL Error!
       │ [SSL: HTTP_REQUEST]
       ▼
┌─────────────────────┐
│  Default Error      │
│  Handler            │
└──────┬──────────────┘
       │ Print Full Stack Trace
       ▼
┌─────────────────────┐
│  Console Output     │
│  (20+ lines)        │
│  ❌ Stack Trace     │
│  ❌ Stack Trace     │
│  ❌ Stack Trace     │
│  ❌ Stack Trace     │
│  ❌ Stack Trace     │
└─────────────────────┘
```

**Result**: ❌ Console spam, difficult to monitor

---

## HTTP Request to HTTPS Server (After Fix)

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP Request
       │ (No SSL Handshake)
       ▼
┌─────────────────────┐
│  Eventlet WSGI      │
│  SSL Layer          │
└──────┬──────────────┘
       │ SSL Error!
       │ [SSL: HTTP_REQUEST]
       ▼
┌─────────────────────┐
│  Custom Error       │
│  Handler            │
│  (Monkey-Patched)   │
└──────┬──────────────┘
       │ Detect SSL Error
       │ Check Rate Limit
       ▼
┌─────────────────────┐
│  Rate Limiter       │
│  (10 sec window)    │
└──────┬──────────────┘
       │ Count Errors
       │ Log if needed
       ▼
┌─────────────────────┐
│  Console Output     │
│  (Concise)          │
│  ⚠️  SSL Protocol   │
│     Mismatch        │
│     Detected        │
└─────────────────────┘
```

**Result**: ✅ Clean output, easy to monitor

---

## Error Handler Decision Tree

```
                    ┌─────────────────┐
                    │  Error Occurs   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Is SSL Error?  │
                    └────┬───────┬────┘
                         │       │
                    Yes  │       │  No
                         │       │
                         ▼       ▼
            ┌──────────────┐  ┌──────────────────┐
            │ HTTP_REQUEST │  │ Use Original     │
            │ error?       │  │ Error Handler    │
            └────┬───┬─────┘  └──────────────────┘
                 │   │
            Yes  │   │  No
                 │   │
                 ▼   ▼
    ┌──────────────┐  ┌──────────────────┐
    │ Check Rate   │  │ Use Original     │
    │ Limit        │  │ Error Handler    │
    └────┬─────────┘  └──────────────────┘
         │
         ▼
    ┌──────────────────┐
    │ Time since last  │
    │ log >= 10 sec?   │
    └────┬───────┬─────┘
         │       │
    Yes  │       │  No
         │       │
         ▼       ▼
┌──────────────┐  ┌──────────────┐
│ Log Concise  │  │ Increment    │
│ Message      │  │ Counter Only │
└──────────────┘  └──────────────┘
```

---

## Rate Limiting Behavior

### Timeline Example

```
Time    Event                           Action
────────────────────────────────────────────────────────────
0:00    HTTP request #1                 Log: "1 request(s)"
0:02    HTTP request #2                 Count only (no log)
0:04    HTTP request #3                 Count only (no log)
0:06    HTTP request #4                 Count only (no log)
0:08    HTTP request #5                 Count only (no log)
0:10    HTTP request #6                 Log: "6 request(s)"
0:12    HTTP request #7                 Count only (no log)
0:15    HTTP request #8                 Count only (no log)
0:20    HTTP request #9                 Log: "3 request(s)"
```

### State Management

```
ssl_error_state = {
    "count": 0,           # Number of errors since last log
    "last_logged": 0      # Timestamp of last log message
}

On each error:
1. Increment count
2. Check if 10 seconds elapsed
3. If yes: Log message, reset count
4. If no: Just increment count
```

---

## Server Startup Flow

```
┌─────────────────────┐
│  python app.py      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Load .env          │
│  FLASK_USE_SSL=?    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  SSL Enabled?       │
└────┬───────┬────────┘
     │       │
Yes  │       │  No
     │       │
     ▼       ▼
┌──────────┐  ┌──────────────┐
│ Check    │  │ Start HTTP   │
│ Certs    │  │ Server       │
└────┬─────┘  └──────────────┘
     │
     ▼
┌──────────────────────┐
│ Certs Exist?         │
└────┬───────┬─────────┘
     │       │
Yes  │       │  No
     │       │
     ▼       ▼
┌──────────┐  ┌──────────────┐
│ Apply    │  │ Fallback to  │
│ SSL      │  │ HTTP         │
│ Patch    │  └──────────────┘
└────┬─────┘
     │
     ▼
┌──────────────────────┐
│ Start HTTPS Server   │
│ with Error Handling  │
└──────────────────────┘
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              Flask-SocketIO                     │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
└───────────────────┼──────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  Eventlet WSGI Server                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         HttpProtocol.handle_error()             │    │
│  │         (Monkey-Patched)                        │    │
│  │                                                  │    │
│  │  ┌──────────────────────────────────────┐      │    │
│  │  │  custom_handle_error()               │      │    │
│  │  │  - Detect SSL errors                 │      │    │
│  │  │  - Rate limit logging                │      │    │
│  │  │  - Suppress stack traces             │      │    │
│  │  └──────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                      SSL Layer                           │
│  - Certificate validation                                │
│  - TLS handshake                                         │
│  - Protocol negotiation                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Error Message Format

### Before (Stack Trace)

```
ssl.SSLError: [SSL: HTTP_REQUEST] http request (_ssl.c:2580)
(2072967) accepted ('127.0.0.1', 40242)
Traceback (most recent call last):
  File "/eventlet/hubs/hub.py", line 471, in fire_timers
    timer()
  File "/eventlet/hubs/timer.py", line 59, in __call__
    cb(*args, **kw)
  File "/eventlet/greenthread.py", line 264, in main
    result = function(*args, **kwargs)
  File "/eventlet/wsgi.py", line 860, in process_request
    proto.__init__(conn_state, self)
  File "/eventlet/wsgi.py", line 359, in __init__
    self.handle()
  File "/eventlet/wsgi.py", line 392, in handle
    self.handle_one_request()
  File "/eventlet/wsgi.py", line 426, in handle_one_request
    self.raw_requestline = self._read_request_line()
  File "/eventlet/wsgi.py", line 407, in _read_request_line
    line = self.rfile.readline(self.server.url_length_limit)
  File "/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
  File "/eventlet/green/ssl.py", line 265, in recv_into
    return self._base_recv(nbytes, flags, into=True, buffer_=buffer)
  File "/eventlet/green/ssl.py", line 280, in _base_recv
    read = self.read(nbytes, buffer_)
  File "/eventlet/green/ssl.py", line 196, in read
    return self._call_trampolining(
  File "/eventlet/green/ssl.py", line 166, in _call_trampolining
    return func(*a, **kw)
  File "/ssl.py", line 1103, in read
    return self._sslobj.read(len, buffer)
ssl.SSLError: [SSL: HTTP_REQUEST] http request (_ssl.c:2580)
```

### After (Concise Message)

```
⚠️  SSL Protocol Mismatch Detected
   5 HTTP request(s) to HTTPS server (rejected)
   Clients must use HTTPS URLs to connect
```

---

## Performance Impact

### Successful Requests (HTTPS)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │────▶│  SSL    │────▶│  Flask  │
└─────────┘     └─────────┘     └─────────┘
                                      │
                                      ▼
                                 ┌─────────┐
                                 │Response │
                                 └─────────┘

Impact: NONE (error handler not invoked)
```

### Failed Requests (HTTP to HTTPS)

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ Client  │────▶│  SSL    │────▶│  Error   │
└─────────┘     └─────────┘     │ Handler  │
                                 └────┬─────┘
                                      │
                                      ▼
                                 ┌─────────┐
                                 │ < 1ms   │
                                 └─────────┘

Impact: < 1ms per error (negligible)
```

---

## Configuration Options

### Enable/Disable SSL

```
.env file:
┌────────────────────────┐
│ FLASK_USE_SSL=True     │  ──▶  HTTPS + Error Handling
│ FLASK_USE_SSL=False    │  ──▶  HTTP (no error handling)
└────────────────────────┘
```

### Adjust Rate Limiting

```
app.py (line 1814):
┌────────────────────────────────────────────┐
│ if current_time - last_logged >= 10:       │  ──▶  10 seconds
│ if current_time - last_logged >= 30:       │  ──▶  30 seconds
│ if current_time - last_logged >= 60:       │  ──▶  60 seconds
└────────────────────────────────────────────┘
```

---

## Summary

### Key Points

1. **Automatic**: Error handling activates when SSL is enabled
2. **Transparent**: No impact on successful requests
3. **Rate-Limited**: Prevents log flooding
4. **User-Friendly**: Clear, concise error messages
5. **Maintainable**: Simple implementation, well-documented

### Benefits

- ✅ Clean console output
- ✅ Easy monitoring
- ✅ Professional appearance
- ✅ Minimal performance impact
- ✅ No breaking changes

---

## Related Documentation

- [SSL Configuration Guide](SSL_CONFIGURATION.md)
- [SSL Quick Start](SSL_QUICK_START.md)
- [SSL Error Handling Guide](SSL_ERROR_HANDLING.md)
- [Implementation Details](SSL_ERROR_HANDLING_IMPLEMENTATION.md)
