import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import Layout from '@/components/Layout/Layout';
import RequireAuth from '@/components/Auth/RequireAuth';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import DocumentsPage from '@/pages/Documents/DocumentsPage';
import DocumentUpload from '@/pages/Documents/DocumentUpload';
import DocumentLibrary from '@/pages/Documents/DocumentLibrary';
import ValidationResults from '@/pages/Documents/ValidationResults';
import ValidationRules from '@/pages/Validation/ValidationRules';
import ValidationAnalytics from '@/pages/Validation/ValidationAnalytics';
import ReportsPage from '@/pages/Reports/ReportsPage';
import ComplianceReports from '@/pages/Reports/ComplianceReports';
import AuditTrail from '@/pages/Reports/AuditTrail';
import AnalyticsDashboard from '@/pages/Reports/AnalyticsDashboard';
import UserManagement from '@/pages/Admin/UserManagement';
import CompanyManagement from '@/pages/Admin/CompanyManagement';
import SystemSettings from '@/pages/Admin/SystemSettings';
import SecurityPage from '@/pages/Admin/SecurityPage';
import Profile from '@/pages/Profile';
import Settings from '@/pages/Settings';
import Notifications from '@/pages/Notifications';
import NotFound from '@/pages/NotFound';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout>
                <Navigate to="/dashboard" replace />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Layout>
                <Dashboard />
              </Layout>
            </RequireAuth>
          }
        />

        {/* Documents Routes */}
        <Route
          path="/documents/*"
          element={
            <RequireAuth permission="document:read">
              <Layout>
                <DocumentsPage />
              </Layout>
            </RequireAuth>
          }
        />

        {/* Document Sub-routes handled by DocumentsPage component */}

        {/* Validation Routes */}
        <Route
          path="/validation/rules"
          element={
            <RequireAuth permission="validation:write">
              <Layout>
                <ValidationRules />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/validation/analytics"
          element={
            <RequireAuth permission="validation:read">
              <Layout>
                <ValidationAnalytics />
              </Layout>
            </RequireAuth>
          }
        />

        {/* Reports Routes */}
        <Route
          path="/reports/*"
          element={
            <RequireAuth permission="report:read">
              <Layout>
                <ReportsPage />
              </Layout>
            </RequireAuth>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin/users"
          element={
            <RequireAuth permission="user:write">
              <Layout>
                <UserManagement />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/admin/companies"
          element={
            <RequireAuth permission="company:write">
              <Layout>
                <CompanyManagement />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/admin/settings"
          element={
            <RequireAuth permission="system:write">
              <Layout>
                <SystemSettings />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/admin/security"
          element={
            <RequireAuth permission="security:read">
              <Layout>
                <SecurityPage />
              </Layout>
            </RequireAuth>
          }
        />

        {/* User Routes */}
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Layout>
                <Profile />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/settings"
          element={
            <RequireAuth>
              <Layout>
                <Settings />
              </Layout>
            </RequireAuth>
          }
        />

        <Route
          path="/notifications"
          element={
            <RequireAuth permission="notification:read">
              <Layout>
                <Notifications />
              </Layout>
            </RequireAuth>
          }
        />

        {/* 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>

      {/* React Query Devtools - Remove in production */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export default App;