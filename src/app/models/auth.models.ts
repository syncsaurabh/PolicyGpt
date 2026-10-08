import { UserRead, UserRole } from './user.models';

/**
 * Payload for logging in via POST /api/v1/auth/login.
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Token response returned upon successful authentication.
 */
export interface Token {
  access_token: string;
  token_type: string;
  user?: UserRead | null;
}

/**
 * Payload for registering a new user via POST /api/v1/auth/register.
 */
export interface UserCreate {
  name: string;
  email: string;
  password: string;
  role?: UserRole | string | null;
}

/**
 * Payload for verifying email OTP via POST /api/v1/auth/verify-otp.
 */
export interface VerifyOTPRequest {
  email: string;
  otp: string;
}

/**
 * Payload for resending email OTP via POST /api/v1/auth/resend-otp.
 */
export interface ResendOTPRequest {
  email: string;
}

/**
 * Request payload for initiating password recovery via POST /api/v1/auth/forgot-password.
 */
export interface ForgotPasswordRequest {
  email: string;
}

/**
 * Response payload from POST /api/v1/auth/forgot-password.
 */
export interface ForgotPasswordResponse {
  message: string;
  reset_token?: string | null;
}

/**
 * Request payload for completing password recovery via POST /api/v1/auth/reset-password.
 */
export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

/**
 * Generic message response schema returned by backend.
 */
export interface MessageResponse {
  message: string;
}

/**
 * Validation error item returned from FastAPI 422 responses.
 */
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
  input?: any;
  ctx?: Record<string, any>;
}

/**
 * HTTPValidationError schema for 422 Unprocessable Entity.
 */
export interface HTTPValidationError {
  detail?: ValidationError[] | string;
}
