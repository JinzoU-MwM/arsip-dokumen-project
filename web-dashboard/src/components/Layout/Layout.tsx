import React, { useState } from 'react';
import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { BrowserRouter as Router } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import Header from './Header';
import Sidebar from './Sidebar';
import useAuthStore from '@/store/authStore';
import RequireAuth from '@/components/Auth/RequireAuth';
import { useMediaQuery } from '@mui/material';

interface LayoutProps {
  children: React.ReactNode;
}

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f1f1',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#c1c1c1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#a8a8a8',
          },
        },
      },
    },
  },
});

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isAuthenticated, isLoading } = useAuthStore();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
            backgroundColor: 'background.default',
          }}
        >
          <Box>Loading...</Box>
        </Box>
      </ThemeProvider>
    );
  }

  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          {children}
        </Router>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Header title="Legal Document Automation System" />

          <Sidebar
            open={sidebarOpen}
            onClose={handleSidebarClose}
            width={isMobile ? 280 : 320}
          />

          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              mt: '64px', // Height of the AppBar
              width: { md: `calc(100% - 320px)` }, // Subtract sidebar width on desktop
              ml: { md: '320px' }, // Add margin on desktop to account for sidebar
              backgroundColor: 'background.default',
              minHeight: 'calc(100vh - 64px)',
            }}
          >
            <RequireAuth>
              {children}
            </RequireAuth>
          </Box>
        </Box>

        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4aed88',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </Router>
    </ThemeProvider>
  );
};

export default Layout;