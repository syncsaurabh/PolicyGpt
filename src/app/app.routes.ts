import { Routes } from '@angular/router';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout';
import { DashboardLayout } from './layouts/dashboard-layout/dashboard-layout';
import { authGuard, noAuthGuard } from './core/guards/auth-guard';
import { roleGuard } from './core/guards/role-guard';
import { Role } from './models/role.model';
import { Auth } from './core/services/auth';

export const routes: Routes = [
    // 1. Public Citizen Dashboard & Public Browse Routes (accessible without login)
    {
        path: '',
        redirectTo: 'citizen',
        pathMatch: 'full'
    },
    {
        path: 'citizen',
        loadComponent: () => import('./features/public/citizen-dashboard/citizen-dashboard.component').then((m) => m.CitizenDashboardComponent)
    },
    {
        path: 'public/policies',
        loadComponent: () => import('./features/public/public-policies/public-policies.component').then((m) => m.PublicPoliciesComponent)
    },
    {
        path: 'public/policies/:id',
        loadComponent: () => import('./features/public/public-details/public-details.component').then((m) => m.PublicDetailsComponent)
    },
    {
        path: 'public/schemes',
        loadComponent: () => import('./features/public/public-schemes/public-schemes.component').then((m) => m.PublicSchemesComponent)
    },
    {
        path: 'public/schemes/:id',
        loadComponent: () => import('./features/public/public-details/public-details.component').then((m) => m.PublicDetailsComponent)
    },
    {
        path: 'public/faqs',
        loadComponent: () => import('./features/public/public-faqs/public-faqs.component').then((m) => m.PublicFaqsComponent)
    },
    {
        path: 'faqs',
        redirectTo: 'public/faqs',
        pathMatch: 'full'
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
            },
            {
                path: 'verify-email',
                loadComponent: () => import('./features/auth/verify-email/verify-email').then((m) => m.VerifyEmail)
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
                children: [
                    {
                        path: '',
                        loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard)
                    },
                    {
                        path: 'admin',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR] },
                        loadComponent: () => import('./features/dashboard/admin-dashboard/admin-dashboard.component').then((m) => m.AdminDashboardComponent)
                    },
                    {
                        path: 'government',
                        canActivate: [roleGuard],
                        data: { roles: [Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/dashboard/government-dashboard/government-dashboard.component').then((m) => m.GovernmentDashboardComponent)
                    },
                    {
                        path: 'citizen',
                        canActivate: [roleGuard],
                        data: { roles: [Role.CITIZEN] },
                        loadComponent: () => import('./features/dashboard/citizen-dashboard/citizen-dashboard.component').then((m) => m.CitizenDashboardComponent)
                    }
                ]
            },
            {
                path: 'policies',
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.CITIZEN, Role.RESEARCHER, Role.ORGANIZATION, Role.GUEST] },
                children: [
                    {
                        path: '',
                        loadComponent: () => import('./features/policies/policies').then((m) => m.Policies)
                    },
                    {
                        path: 'upload',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/policies/upload-policy/upload-policy').then((m) => m.UploadPolicy)
                    },
                    {
                        path: ':id',
                        loadComponent: () => import('./features/policies/policy-details/policy-details').then((m) => m.PolicyDetails)
                    },
                    {
                        path: ':id/edit',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/policies/edit-policy/edit-policy').then((m) => m.EditPolicy)
                    },
                    {
                        path: ':id/submit',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/policies/submit-policy/submit-policy').then((m) => m.SubmitPolicy)
                    },
                    {
                        path: ':id/status',
                        loadComponent: () => import('./features/policies/policy-status/policy-status').then((m) => m.PolicyStatusComponent)
                    },
                    {
                        path: ':id/archive',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR] },
                        loadComponent: () => import('./features/policies/policy-archive/policy-archive').then((m) => m.PolicyArchive)
                    },
                    {
                        path: ':id/submitted',
                        loadComponent: () => import('./features/policies/policy-submitted/policy-submitted').then((m) => m.PolicySubmitted)
                    }
                ]
            },
            {
                path: 'schemes',
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.CITIZEN, Role.RESEARCHER, Role.ORGANIZATION, Role.GUEST] },
                children: [
                    {
                        path: '',
                        loadComponent: () => import('./features/schemes/schemes').then((m) => m.Schemes)
                    },
                    {
                        path: 'create',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/schemes/create-scheme/create-scheme').then((m) => m.CreateScheme)
                    },
                    {
                        path: ':id',
                        loadComponent: () => import('./features/schemes/scheme-details/scheme-details').then((m) => m.SchemeDetails)
                    },
                    {
                        path: ':id/edit',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/schemes/edit-scheme/edit-scheme').then((m) => m.EditScheme)
                    }
                ]
            },
            {
                path: 'search',
                canActivate: [roleGuard],
                data: { roles: [Role.CITIZEN, Role.RESEARCHER, Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.ORGANIZATION, Role.GUEST] },
                loadComponent: () => import('./features/policies/policies').then((m) => m.Policies)
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
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.CITIZEN, Role.RESEARCHER, Role.ORGANIZATION] }
            },
            {
                path: 'approvals',
                loadComponent: () => import('./features/approvals/approvals').then((m) => m.Approvals),
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] }
            },
            {
                path: 'reports',
                loadComponent: () => import('./features/reports/reports').then((m) => m.Reports),
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] }
            },
            {
                path: 'feedback',
                canActivate: [roleGuard],
                data: { roles: [Role.CITIZEN, Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.RESEARCHER, Role.ORGANIZATION] },
                loadComponent: () => import('./features/feedback/feedback').then((m) => m.Feedback)
            },

            // Admin specific routes
            {
                path: 'admin',
                canActivate: [roleGuard],
                data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                children: [
                    {
                        path: 'users',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR] },
                        loadComponent: () => import('./features/admin/users/users').then((m) => m.Users)
                    },
                    {
                        path: 'faqs',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL] },
                        loadComponent: () => import('./features/admin/faqs/admin-faqs.component').then((m) => m.AdminFaqsComponent)
                    },
                    {
                        path: 'audit-logs',
                        canActivate: [roleGuard],
                        data: { roles: [Role.ADMINISTRATOR] },
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