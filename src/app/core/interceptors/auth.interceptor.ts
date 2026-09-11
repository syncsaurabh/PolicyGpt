import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Functional interceptor to attach Bearer token to headers of protected API requests
 * and handle authentication expiration and API errors cleanly.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // List of public endpoints that do not require Authorization header
  const publicEndpoints = [
    '/auth/login',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/health'
  ];

  const isPublic = publicEndpoints.some((url) => req.url.includes(url));
  const token = authService.getToken();

  let authReq = req;
  if (!isPublic && token) {
    authReq = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // 401 Unauthorized: Session expired or invalid token
      if (error.status === 401) {
        // Prevent redirect loop if already on login page
        if (!router.url.includes('/login') && !isPublic) {
          authService.logout(false);
          router.navigate(['/login'], {
            queryParams: { returnUrl: router.url, sessionExpired: 'true' }
          });
        }
      }

      return throwError(() => error);
    })
  );
};
