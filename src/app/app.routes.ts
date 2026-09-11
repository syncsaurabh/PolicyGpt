import { Routes } from '@angular/router';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout';
import { DashboardLayout } from './layouts/dashboard-layout/dashboard-layout';
import { authGuard, noAuthGuard } from './core/guards/auth-guard';
import { roleGuard } from './core/guards/role-guard';
import { Role } from './models/role.model';

export const routes: Routes = [
    // 1. Public Citizen Dashboard route (accessible without login)
    {
        path: '',
        redirectTo: 'citizen',
        pathMatch: 'full'
    },
    {
        path: 'citizen',
        loadComponent: () => import('./features/public/citizen-dashboard/citizen-dashboard.component').then((m) => m.CitizenDashboardComponent)
    },

    // 2. Public Auth routes (inside AuthLayoutComponent)
    {


        path: '',
        component: AuthLayoutComponent,
        canActivate: [noAuthGuard], // If authenticated, redirect auth pages to /dashboard
        children: [
            {
                path: 'login',
                loadComponent: () => import('./features/auth/login/login').then((m) => m.Login)
            },
            {
                path: 'register',
                loadComponent: () => import('./features/auth/register/register').then((m) => m.Register)
            },
            {
                path: 'forgot-password',
                loadComponent: () => import('./features/auth/forgot-password/forgot-password').then((m) => m.ForgotPassword)
            },
            {
                path: 'reset-password',
                loadComponent: () => import('./features/auth/reset-password/reset-password').then((m) => m.ResetPassword)
            }
        ]
    },

    // 2. Protected routes (inside DashboardLayout)
    {
        path: '',
        component: DashboardLayout,
        canActivate: [authGuard], // Must be logged in to view dashboard layout
        children: [
            {
                path: 'dashboard',
                loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard)
            },
            {
                path: 'policies',
                loadComponent: () => import('./features/policies/policies').then((m) => m.Policies),
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.RESEARCHER] }
            },
            {
                path: 'schemes',
                loadComponent: () => import('./features/schemes/schemes').then((m) => m.Schemes),
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.CITIZEN] }
            },
            {
                path: 'eligibility',
                loadComponent: () => import('./features/eligibility/eligibility').then((m) => m.Eligibility),
                canActivate: [roleGuard],
                data: { roles: [Role.CITIZEN] }
            },
            {
                path: 'compare',
                loadComponent: () => import('./features/compare/compare').then((m) => m.Compare),
                canActivate: [roleGuard],
                data: { roles: [Role.CITIZEN, Role.RESEARCHER] }
            },
            {
                path: 'notifications',
                loadComponent: () => import('./features/notifications/notifications').then((m) => m.Notifications),
                canActivate: [roleGuard],
                data: { roles: [Role.CITIZEN] }
            },
            {
                path: 'approvals',
                loadComponent: () => import('./features/approvals/approvals').then((m) => m.Approvals),
                canActivate: [roleGuard],
                data: { roles: [Role.GOVERNMENT_OFFICIAL] }
            },
            {
                path: 'reports',
                loadComponent: () => import('./features/reports/reports').then((m) => m.Reports),
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.RESEARCHER] }
            },
            {
                path: 'feedback',
                loadComponent: () => import('./features/feedback/feedback').then((m) => m.Feedback)
            },

            // Admin specific routes
            {
                path: 'admin',
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR] },
                children: [
                    {
                        path: 'users',
                        loadComponent: () => import('./features/admin/users/users').then((m) => m.Users)
                    },
                    {
                        path: 'audit-logs',
                        loadComponent: () => import('./features/admin/audit-logs/audit-logs').then((m) => m.AuditLogs)
                    }
                ]
            },

            // Access Denied / Unauthorized page
            {
                path: 'unauthorized',
                loadComponent: () => import('./features/unauthorized/unauthorized').then((m) => m.Unauthorized)
            }
        ]
    },

    // 3. Fallbacks and Redirections
    {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
    },
    {
        path: '**',
        redirectTo: 'dashboard'
    }
];