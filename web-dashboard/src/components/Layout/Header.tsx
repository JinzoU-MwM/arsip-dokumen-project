import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  AccountCircle,
  Notifications,
  Settings,
  Logout,
  Security,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

interface HeaderProps {
  title?: string;
}

const Header: React.FC<HeaderProps> = ({ title = 'Dashboard' }) => {
  const navigate = useNavigate();
  const { user, logout, hasPermission } = useAuthStore();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setNotificationAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Failed to logout');
    }
    handleMenuClose();
  };

  const handleProfile = () => {
    navigate('/profile');
    handleMenuClose();
  };

  const handleSettings = () => {
    navigate('/settings');
    handleMenuClose();
  };

  const handleSecurity = () => {
    navigate('/security');
    handleMenuClose();
  };

  const isMenuOpen = Boolean(anchorEl);
  const isNotificationMenuOpen = Boolean(notificationAnchorEl);

  const menuId = 'primary-search-account-menu';
  const notificationMenuId = 'primary-search-notification-menu';

  return (
    <AppBar position="sticky" elevation={1}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notifications */}
          {hasPermission('notification:read') && (
            <Tooltip title="Notifications">
              <IconButton
                size="large"
                aria-label="show notifications"
                aria-controls={notificationMenuId}
                aria-haspopup="true"
                onClick={handleNotificationMenuOpen}
                color="inherit"
              >
                <Badge badgeContent={3} color="error">
                  <Notifications />
                </Badge>
              </IconButton>
            </Tooltip>
          )}

          {/* User Profile */}
          <Tooltip title="Profile">
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls={menuId}
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
              <Avatar
                sx={{ width: 32, height: 32 }}
                src={user?.avatar}
                alt={user?.fullName}
              >
                {user?.fullName?.charAt(0)?.toUpperCase()}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={isMenuOpen}
        onClose={handleMenuClose}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" noWrap>
            {user?.fullName}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {user?.email}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Role: {user?.role?.replace('_', ' ')}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleProfile}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        {hasPermission('system:read') && (
          <MenuItem onClick={() => { navigate('/dashboard'); handleMenuClose(); }}>
            <ListItemIcon>
              <DashboardIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Dashboard</ListItemText>
          </MenuItem>
        )}
        {hasPermission('system:write') && (
          <MenuItem onClick={handleSettings}>
            <ListItemIcon>
              <Settings fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>
        )}
        {hasPermission('audit:read') && (
          <MenuItem onClick={handleSecurity}>
            <ListItemIcon>
              <Security fontSize="small" />
            </ListItemIcon>
            <ListItemText>Security</ListItemText>
          </MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationAnchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={isNotificationMenuOpen}
        onClose={handleMenuClose}
      >
        <Box sx={{ px: 2, py: 1, minWidth: 300 }}>
          <Typography variant="subtitle2">Notifications</Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleMenuClose}>
          <ListItemText
            primary="New document uploaded"
            secondary="Company ABC - KTP document"
          />
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemText
            primary="Validation completed"
            secondary="5 documents validated successfully"
          />
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemText
            primary="Security alert"
            secondary="Multiple failed login attempts detected"
            secondaryTypographyProps={{ color: 'error' }}
          />
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => { navigate('/notifications'); handleMenuClose(); }}>
          <ListItemText
            primary="View all notifications"
            sx={{ textAlign: 'center', color: 'primary.main' }}
          />
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default Header;