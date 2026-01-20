# Authentication System - Implementation Guide

This document provides an overview of the enterprise-grade authentication system implemented in this project.

---

## 🎯 Features Implemented

✅ **Protected Routes** - All dashboard routes require authentication  
✅ **Enterprise UI** - Professional login page with dark/light mode support  
✅ **Responsive Design** - Mobile-first, works on all screen sizes  
✅ **Form Validation** - Client-side validation with server-side error handling  
✅ **Loading States** - Skeleton loaders and loading spinners  
✅ **Security** - JWT tokens in httpOnly cookies + CSRF protection  
✅ **Edge Case Handling** - Token expiration, network errors, infinite loops prevention  

---

## 📁 File Structure

```
src/
├── contexts/
│   └── AuthContext.jsx          # Authentication context provider
├── components/
│   ├── ProtectedRoute.jsx       # Route guard component
│   └── TopBar.jsx               # Updated with logout functionality
├── pages/
│   └── Login.jsx                # Login page
├── api/
│   └── http.js                  # Axios instance with CSRF handling
└── routes/
    └── AppRoutes.jsx             # Updated with protected routes

fake server/
├── server.js                     # Mock auth endpoints
└── BACKEND_API_SPEC.md          # Backend implementation guide
```

---

## 🔐 Authentication Flow

### 1. Initial Load
```
User visits app → AuthContext checks /auth/me → 
  If authenticated → Show dashboard
  If not → Redirect to /login
```

### 2. Login Process
```
1. User enters credentials
2. Frontend validates (client-side)
3. GET /api/auth/csrf → Get CSRF token
4. POST /api/auth/login → Authenticate
5. Server sets httpOnly cookie with JWT
6. Server sets XSRF-TOKEN cookie
7. Frontend receives user data
8. Redirect to dashboard
```

### 3. Protected Routes
```
User navigates → ProtectedRoute checks AuthContext →
  If authenticated → Render page
  If not → Redirect to /login (preserving intended destination)
```

### 4. Logout Process
```
User clicks logout → POST /api/auth/logout →
  Server clears session → Clears cookies →
  Frontend clears state → Redirect to /login
```

---

## 🛡️ Security Features

### JWT in httpOnly Cookies
- **Why**: Prevents XSS attacks from stealing tokens
- **Implementation**: Server sets `authToken` cookie with `httpOnly: true`
- **Access**: Only server can read, browser sends automatically

### CSRF Protection
- **Why**: Prevents cross-site request forgery attacks
- **Implementation**: 
  - Server generates CSRF token
  - Frontend reads from `XSRF-TOKEN` cookie
  - Frontend sends in `X-XSRF-TOKEN` header for POST/PUT/DELETE
  - Server validates token matches session

### Token Expiration
- **Duration**: 24 hours
- **Handling**: 401 errors trigger automatic logout
- **Refresh**: Optional `/api/auth/refresh` endpoint

---

## 🎨 UI Components

### Login Page
- **Design**: Enterprise-grade, matches app theme
- **Features**:
  - Email/password validation
  - Show/hide password toggle
  - Loading states
  - Error messages
  - Demo credentials display
  - Responsive layout

### TopBar
- **User Menu**: Shows user name/email
- **Logout**: Integrated logout functionality
- **Avatar**: Shows user initials

### ProtectedRoute
- **Loading State**: Shows spinner while checking auth
- **Redirect**: Preserves intended destination

---

## 🧪 Testing

### Demo Credentials
```
Email: admin@example.com
Password: admin123
```

### Test Flow
1. Start fake server: `cd fake\ server && npm install && npm start`
2. Start frontend: `npm run dev`
3. Visit `http://localhost:5173`
4. Should redirect to `/login`
5. Enter demo credentials
6. Should redirect to dashboard
7. Try accessing `/services` directly - should work
8. Click logout - should redirect to login
9. Try accessing `/services` directly - should redirect to login

---

## 🐛 Edge Cases Handled

### 1. Token Expiration
- **Issue**: User's token expires while using app
- **Solution**: Axios interceptor catches 401, automatically logs out

### 2. Infinite Loop Prevention
- **Issue**: Logout might trigger 401, causing loop
- **Solution**: Flag prevents multiple simultaneous logout calls

### 3. Network Errors
- **Issue**: Network failure during login
- **Solution**: Error handling shows user-friendly messages

### 4. Already Authenticated
- **Issue**: User visits `/login` when already logged in
- **Solution**: Redirects to dashboard automatically

### 5. Stale Cookies
- **Issue**: Old cookies from previous session
- **Solution**: Server validates token, clears invalid ones

### 6. CSRF Token Missing
- **Issue**: CSRF token not available
- **Solution**: Request new token before login

---

## 🔧 Configuration

### Frontend (`src/api/http.js`)
```javascript
baseURL: "http://localhost:8080/api"
withCredentials: true  // Enables cookie sending
```

### Fake Server (`fake server/server.js`)
```javascript
CORS: {
  origin: "http://localhost:5173",
  credentials: true
}
```

---

## 📝 Backend Integration

When backend is ready, refer to:
- `fake server/BACKEND_API_SPEC.md` - Complete API specification
- Replace fake server endpoints with real backend
- Ensure same cookie configuration
- Ensure same CSRF token flow

---

## 🚀 Production Checklist

Before deploying to production:

- [ ] Set `secure: true` on cookies (HTTPS required)
- [ ] Use real JWT library (not base64 mock)
- [ ] Implement password hashing (bcrypt/argon2)
- [ ] Use Redis/database for sessions (not in-memory)
- [ ] Add rate limiting on login endpoint
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Add logging for security events
- [ ] Implement password reset flow
- [ ] Add account lockout after failed attempts

---

## 🐛 Troubleshooting

### Issue: Login redirects immediately
**Solution**: Check browser console for errors, verify fake server is running

### Issue: CSRF token errors
**Solution**: Ensure `XSRF-TOKEN` cookie is being set, check CORS configuration

### Issue: Cookies not being sent
**Solution**: Verify `withCredentials: true` in axios config, check CORS allows credentials

### Issue: 401 errors on every request
**Solution**: Check token expiration, verify cookie is being set correctly

---

## 📚 Additional Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [CSRF Protection](https://owasp.org/www-community/attacks/csrf)

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0.0
