import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';
import apiService from '@/services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await apiService.login(username, password);

          if (response.success && response.data) {
            const { user } = response.data;
            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            throw new Error(response.error || 'Login failed');
          }
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message,
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });

        try {
          await apiService.logout();
        } catch (error) {
          // Continue with logout even if API call fails
          console.error('Logout API call failed:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      refreshToken: async () => {
        try {
          await apiService.refreshToken();
          const user = apiService.getCurrentUser();
          set({ user });
        } catch (error) {
          // If refresh fails, log out
          get().logout();
        }
      },

      clearError: () => set({ error: null }),

      hasPermission: (permission: string) => {
        const { user } = get();
        return user?.permissions?.includes(permission) || false;
      },

      hasRole: (role: string) => {
        const { user } = get();
        return user?.role === role;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Hook to check authentication status
export const useRequireAuth = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return { loading: true, authenticated: false };
  }

  return { loading: false, authenticated: isAuthenticated };
};

// Hook to get current user info
export const useCurrentUser = () => {
  const { user, isAuthenticated, isLoading } = useAuthStore();

  return {
    user,
    isAuthenticated,
    isLoading,
  };
};

// Permission-based access control hook
export const usePermissions = () => {
  const { hasPermission, hasRole, user } = useAuthStore();

  return {
    hasPermission,
    hasRole,
    isAdmin: user?.role === 'admin',
    isLegalAdmin: user?.role === 'legal_admin',
    isCompanyUser: user?.role === 'company_user',
    isViewer: user?.role === 'viewer',
    user,
  };
};