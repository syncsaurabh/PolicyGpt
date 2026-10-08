import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { finalize } from 'rxjs';
import { LoadingService } from '../services/loading.service';

/**
 * Functional HTTP interceptor to track active global HTTP requests
 * and feed real-time loading status to the LoadingService.
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loadingService = inject(LoadingService);

  // Increment active request counter
  loadingService.startRequest();

  return next(req).pipe(
    finalize(() => {
      // Decrement active request counter when request completes or errors
      loadingService.stopRequest();
    })
  );
};
