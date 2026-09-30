# PolicyGPT Frontend & FastAPI Backend Integration Documentation

This document explains the technical architecture, security protocols, API services, and data models used to integrate the Angular frontend (`policy-gpt-frontend`) with the live FastAPI backend.

---

## 1. API Base URL & Environment Configuration

The API base URL is configured centrally in the Angular environment files and injected into all services. **No URLs are hardcoded in components or services.**

- **Development Environment**: [`src/environments/environment.development.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/environments/environment.development.ts)
- **Production Environment**: [`src/environments/environment.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/environments/environment.ts)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api/v1'
};
```

---

## 2. Authentication Flow & Token Handling

The authentication flow utilizes JSON Web Tokens (JWT) adhering to standard OAuth2 Bearer token practices:

1. **User Login (`POST /api/v1/auth/login`)**:
   - The user inputs their email and password.
   - The backend validates credentials and returns a `Token` payload:
     ```json
     {
       "access_token": "<jwt-token>",
       "token_type": "bearer",
       "user": {
         "id": 1,
         "name": "Citizen User",
         "email": "citizen@policygpt.gov.in",
         "role": "CITIZEN",
         "is_active": true,
         "created_at": "...",
         "updated_at": "..."
       }
     }
     ```
2. **Token Storage**:
   - The `access_token` is persisted in `localStorage` under `policy_gpt_token`.
   - The user session profile is saved under `policy_gpt_user`.
3. **Session Management**:
   - User state is managed via reactive Angular Signals: `currentUser` and `authenticated`.
4. **Logout**:
   - `AuthService.logout()` clears credentials and tokens from storage and redirects to `/login`.

---

## 3. JWT Auth Interceptor

The functional interceptor [`authInterceptor`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/interceptors/auth.interceptor.ts) is registered in [`app.config.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/app.config.ts):

- **Selective Authorization**:
  - Automatically skips attaching `Authorization` headers to public endpoints:
    - `/auth/login`
    - `/auth/register`
    - `/auth/forgot-password`
    - `/auth/reset-password`
    - `/health`
  - For protected endpoints (e.g. `/users/me`, `/users/admin/test`, `/users/government/test`), it automatically appends:
    ```http
    Authorization: Bearer <access_token>
    ```
- **Error Interception & 401 Expiration**:
  - Catches `401 Unauthorized` responses on protected routes.
  - Automatically logs out expired sessions and redirects to `/login?sessionExpired=true` without infinite redirect loops.

---

## 4. Role-Based Access Control (RBAC) & Route Guards

### Backend Roles (`UserRole`):
- `ADMINISTRATOR`
- `GOVERNMENT_OFFICIAL`
- `CITIZEN`
- `RESEARCHER`
- `ORGANIZATION`
- `GUEST_USER`

### Angular Guards:
- [`authGuard`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/guards/auth-guard.ts): Restricts routes to authenticated sessions.
- [`roleGuard`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/guards/role-guard.ts): Inspects route metadata `data: { roles: [...] }` and compares against the current user's role using normalized, case-insensitive comparison via `AuthService.hasRole()`.
- Unauthorized requests redirect to `/unauthorized`.

---

## 5. TypeScript Models & OpenAPI Alignment

Located in `src/app/models/`:

| Model File | Interface / Enum | Description |
| :--- | :--- | :--- |
| [`auth.models.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/models/auth.models.ts) | `LoginRequest` | Email and password login body |
| | `Token` | Access token and UserRead response |
| | `UserCreate` | Registration payload |
| | `ForgotPasswordRequest` | Email recovery request |
| | `ForgotPasswordResponse` | Recovery message and optional dev token |
| | `ResetPasswordRequest` | Token and new password payload |
| | `MessageResponse` | General status message response |
| | `HTTPValidationError` | FastAPI 422 validation structure |
| [`user.models.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/models/user.models.ts) | `UserRole` | Official backend role enum |
| | `UserRead` | User schema with id, email, name, role, is_active |
| | `UserUpdate` | Profile update schema (`name`) |
| [`role.model.ts`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/models/role.model.ts) | `normalizeRole()` | Normalization & role conversion helpers |
| | `toDisplayRole()` | Maps backend uppercase to display roles |
| | `toBackendRole()` | Maps display roles to backend uppercase |

---

## 6. Available Angular Services

### [`AuthService`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/services/auth.service.ts)
- `login(credentials: LoginRequest): Observable<Token>`
- `register(userData: UserCreate): Observable<UserRead>`
- `forgotPassword(payload: ForgotPasswordRequest): Observable<ForgotPasswordResponse>`
- `resetPassword(payload: ResetPasswordRequest): Observable<MessageResponse>`
- `fetchProfile(): Observable<UserRead | null>`
- `getToken(): string | null`
- `isAuthenticated(): boolean`
- `hasRole(roles: (Role | UserRole | string)[]): boolean`
- `logout(redirect?: boolean): void`

### [`UserService`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/services/user.service.ts)
- `getMe(): Observable<UserRead>`: Queries `GET /api/v1/users/me`
- `updateMe(payload: UserUpdate): Observable<UserRead>`: Sends `PUT /api/v1/users/me`
- `testAdminRbac(): Observable<any>`: Tests `GET /api/v1/users/admin/test`
- `testGovernmentRbac(): Observable<any>`: Tests `GET /api/v1/users/government/test`

### [`PolicyService`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/services/policy.service.ts) & [`SchemeService`](file:///c:/Users/sks73/OneDrive/Desktop/GPT%20Policy/policy-gpt-frontend/src/app/core/services/scheme.service.ts)
- `checkHealth(): Observable<SystemHealth>`: Queries system health check at `GET /health`

---

## 7. CORS Configuration

The FastAPI backend runs on `http://127.0.0.1:8000` and the Angular frontend runs on `http://localhost:4200`.

Preflight OPTIONS verification confirmed that the FastAPI backend already has CORS configured:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

No changes were made to the backend code.

---

## 8. Running Frontend and Backend Together

### 1. Start the FastAPI Backend:
In the backend directory:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 2. Start the Angular Frontend:
In the `policy-gpt-frontend` directory:
```bash
ng serve
```
- App URL: `http://localhost:4200`
- The Angular app will connect to `http://127.0.0.1:8000/api/v1`.
