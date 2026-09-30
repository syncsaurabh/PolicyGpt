import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { UserRead, UserUpdate } from '../../models/user.models';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = environment.apiUrl;

  /**
   * Retrieve current authenticated user profile via GET /users/me.
   */
  getMe(): Observable<UserRead> {
    return this.http.get<UserRead>(`${this.API_URL}/users/me`);
  }

  /**
   * Update current authenticated user profile via PUT /users/me.
   */
  updateMe(payload: UserUpdate): Observable<UserRead> {
    return this.http.put<UserRead>(`${this.API_URL}/users/me`, payload);
  }

  /**
   * Verify RBAC access for Administrator role via GET /users/admin/test.
   */
  testAdminRbac(): Observable<{ message?: string } | any> {
    return this.http.get<any>(`${this.API_URL}/users/admin/test`);
  }

  /**
   * Verify RBAC access for Government Official role via GET /users/government/test.
   */
  testGovernmentRbac(): Observable<{ message?: string } | any> {
    return this.http.get<any>(`${this.API_URL}/users/government/test`);
  }
}
