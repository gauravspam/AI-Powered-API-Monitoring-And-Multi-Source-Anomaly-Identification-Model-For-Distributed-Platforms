# Backend API Specification - Authentication System

This document describes the authentication API endpoints that need to be implemented by the backend development team. The current implementation in `server.js` is a **mock/fake server** for frontend development purposes.

---

## 🔐 Authentication Flow Overview

```
1. Frontend → GET /api/auth/csrf → Receives CSRF token
2. Frontend → POST /api/auth/login (with CSRF header) → Receives httpOnly cookie with JWT
3. Frontend → All subsequent requests include httpOnly cookie automatically
4. Frontend → POST /api/auth/logout → Clears session and cookies
```

---

## 📋 API Endpoints

### 1. Get CSRF Token

**Endpoint:** `GET /api/auth/csrf`

**Purpose:** Get CSRF token before login to prevent CSRF attacks.

**Request:**
- Headers: None required
- Body: None

**Response:**
- Status: `200 OK`
- Cookies: Sets `XSRF-TOKEN` cookie (httpOnly: false, readable by JS)
- Body:
```json
{
  "csrfToken": "base64-encoded-random-string"
}
```

**Implementation Notes:**
- Generate a random CSRF token (32+ bytes, base64 encoded)
- Store token server-side (in-memory, Redis, or database) with expiration (15 minutes)
- Set `XSRF-TOKEN` cookie with `httpOnly: false` (must be readable by JavaScript)
- Use `SameSite=Strict` for CSRF protection

---

### 2. Login

**Endpoint:** `POST /api/auth/login`

**Purpose:** Authenticate user and create session.

**Request:**
- Headers:
  - `Content-Type: application/json`
  - `X-XSRF-TOKEN: <csrf-token>` (from XSRF-TOKEN cookie)
- Body:
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Response:**

**Success (200 OK):**
- Cookies:
  - `authToken`: JWT token in httpOnly cookie
  - `XSRF-TOKEN`: CSRF token (httpOnly: false)
- Body:
```json
{
  "success": true,
  "user": {
    "id": "1",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Validation Error",
  "message": "Email and password are required"
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Authentication Failed",
  "message": "Invalid email or password"
}
```

**Error (403 Forbidden):**
```json
{
  "error": "Forbidden",
  "message": "Invalid CSRF token"
}
```

**Implementation Notes:**
- Validate email format and password strength
- Verify password against database (use bcrypt/argon2 for hashing)
- Generate JWT token with:
  - `userId` or `sessionId`
  - Expiration: 24 hours
  - Sign with secret key
- Store session server-side (Redis recommended for production)
- Set `authToken` cookie with:
  - `httpOnly: true` (prevents XSS attacks)
  - `secure: true` (in production with HTTPS)
  - `sameSite: strict` (CSRF protection)
  - `maxAge: 86400000` (24 hours)
- Generate new CSRF token and store it
- Set `XSRF-TOKEN` cookie (httpOnly: false)

---

### 3. Get Current User

**Endpoint:** `GET /api/auth/me`

**Purpose:** Get current authenticated user information.

**Request:**
- Headers: None (cookie sent automatically)
- Cookies: `authToken` (httpOnly cookie)

**Response:**

**Success (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "1",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Unauthorized",
  "message": "No authentication token"
}
```
or
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

**Implementation Notes:**
- Extract `authToken` from httpOnly cookie
- Verify JWT signature and expiration
- Check if session exists server-side
- Return user data (exclude sensitive fields like password hash)

---

### 4. Logout

**Endpoint:** `POST /api/auth/logout`

**Purpose:** End user session and clear cookies.

**Request:**
- Headers:
  - `X-XSRF-TOKEN: <csrf-token>` (required for state-changing operations)
- Cookies: `authToken` (httpOnly cookie)

**Response:**

**Success (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Unauthorized",
  "message": "No authentication token"
}
```

**Error (403 Forbidden):**
```json
{
  "error": "Forbidden",
  "message": "Invalid CSRF token"
}
```

**Implementation Notes:**
- Verify JWT token from cookie
- Verify CSRF token from header
- Delete session from server-side storage
- Clear `authToken` cookie
- Clear `XSRF-TOKEN` cookie

---

### 5. Refresh Token (Optional)

**Endpoint:** `POST /api/auth/refresh`

**Purpose:** Refresh JWT token before expiration.

**Request:**
- Headers: None
- Cookies: `authToken` (httpOnly cookie)

**Response:**

**Success (200 OK):**
- Cookies: New `authToken` and `XSRF-TOKEN` cookies
- Body:
```json
{
  "success": true
}
```

**Implementation Notes:**
- Verify current token
- Generate new token with extended expiration
- Update cookies
- Optionally rotate CSRF token

---

## 🔒 Security Requirements

### JWT Token Structure

```json
{
  "userId": "uuid-or-user-id",
  "exp": 1234567890,  // Unix timestamp
  "iat": 1234567890,  // Issued at
  "role": "admin"      // Optional: user role
}
```

**Signing:**
- Use HS256 or RS256 algorithm
- Secret key: Store in environment variable (never commit)
- Minimum key length: 256 bits

### Cookie Configuration

**authToken Cookie:**
```javascript
{
  httpOnly: true,        // Prevents JavaScript access (XSS protection)
  secure: true,          // HTTPS only (in production)
  sameSite: 'strict',    // CSRF protection
  maxAge: 86400000,      // 24 hours (in milliseconds)
  path: '/'              // Available site-wide
}
```

**XSRF-TOKEN Cookie:**
```javascript
{
  httpOnly: false,       // Must be readable by JavaScript
  secure: true,          // HTTPS only (in production)
  sameSite: 'strict',    // CSRF protection
  maxAge: 86400000,      // 24 hours
  path: '/'
}
```

### CSRF Protection

1. **CSRF Token Generation:**
   - Generate random token (32+ bytes)
   - Store server-side with session ID
   - Set expiration (15 minutes for initial, 24 hours after login)

2. **CSRF Token Validation:**
   - Required for all state-changing operations (POST, PUT, DELETE, PATCH)
   - Read token from `X-XSRF-TOKEN` header
   - Compare with server-stored token
   - Reject if mismatch or expired

3. **Exempt Endpoints:**
   - `GET /api/auth/csrf` (public)
   - `GET /api/auth/me` (read-only)
   - `GET /health` (public)

---

## 📊 Database Schema (Recommended)

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sessions Table (Optional - if using database)
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) UNIQUE NOT NULL,
  csrf_token VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

**Alternative:** Use Redis for session storage (recommended for production):
```javascript
// Redis key structure
sessions:<sessionId> = {
  userId: "uuid",
  csrfToken: "token",
  expiresAt: timestamp
}
```

---

## 🧪 Testing Examples

### cURL Examples

**1. Get CSRF Token:**
```bash
curl -X GET http://localhost:8080/api/auth/csrf \
  -c cookies.txt
```

**2. Login:**
```bash
# Extract CSRF token from cookies.txt
CSRF_TOKEN=$(grep XSRF-TOKEN cookies.txt | awk '{print $7}')

curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: $CSRF_TOKEN" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  -c cookies.txt
```

**3. Get Current User:**
```bash
curl -X GET http://localhost:8080/api/auth/me \
  -b cookies.txt
```

**4. Logout:**
```bash
CSRF_TOKEN=$(grep XSRF-TOKEN cookies.txt | awk '{print $7}')

curl -X POST http://localhost:8080/api/auth/logout \
  -H "X-XSRF-TOKEN: $CSRF_TOKEN" \
  -b cookies.txt \
  -c cookies.txt
```

---

## ⚠️ Error Handling

All endpoints should return consistent error responses:

```json
{
  "error": "Error Type",
  "message": "Human-readable error message"
}
```

**HTTP Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: CSRF token invalid or insufficient permissions
- `500 Internal Server Error`: Server error (don't expose details)

---

## 🔄 Frontend Integration

The frontend expects:

1. **Automatic Cookie Handling:**
   - All requests include `withCredentials: true`
   - Browser automatically sends httpOnly cookies

2. **CSRF Token Handling:**
   - Frontend reads `XSRF-TOKEN` cookie
   - Sends token in `X-XSRF-TOKEN` header for POST/PUT/DELETE

3. **Error Handling:**
   - 401 errors trigger automatic logout
   - 403 errors show CSRF error message

---

## 📝 Implementation Checklist

- [ ] Implement JWT token generation and verification
- [ ] Implement password hashing (bcrypt/argon2)
- [ ] Set up session storage (Redis recommended)
- [ ] Implement CSRF token generation and validation
- [ ] Configure httpOnly cookies correctly
- [ ] Add input validation (email format, password strength)
- [ ] Implement rate limiting for login endpoint
- [ ] Add logging for security events
- [ ] Set up HTTPS in production
- [ ] Configure CORS properly (credentials: true)
- [ ] Add password reset functionality (optional)
- [ ] Implement account lockout after failed attempts (optional)

---

## 🚀 Production Considerations

1. **Environment Variables:**
   ```env
   JWT_SECRET=<256-bit-random-secret>
   JWT_EXPIRATION=86400
   CSRF_TOKEN_EXPIRATION=900
   REDIS_URL=redis://localhost:6379
   DATABASE_URL=postgresql://...
   ```

2. **Rate Limiting:**
   - Login endpoint: 5 attempts per 15 minutes per IP
   - Use Redis or middleware like `express-rate-limit`

3. **Monitoring:**
   - Log all authentication attempts
   - Alert on suspicious activity (multiple failed logins)

4. **Security Headers:**
   ```javascript
   app.use(helmet());
   app.use(cors({
     origin: process.env.FRONTEND_URL,
     credentials: true,
   }));
   ```

---

## 📚 Additional Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [CSRF Protection](https://owasp.org/www-community/attacks/csrf)

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0
