import React from 'react';
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Collapse,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  UploadFile,
  Folder,
  Assessment,
  Security,
  Settings,
  People,
  Business,
  Gavel,
  Description,
  ExpandLess,
  ExpandMore,
  History,
  Analytics,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { usePermissions } from '@/store/authStore';
import { NavigationItem } from '@/types';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  width?: number;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'Dashboard',
    path: '/dashboard',
    permissions: ['system:read'],
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: 'Description',
    path: '/documents',
    permissions: ['document:read'],
    children: [
      {
        id: 'upload',
        label: 'Upload',
        icon: 'UploadFile',
        path: '/documents/upload',
        permissions: ['document:write'],
      },
      {
        id: 'library',
        label: 'Document Library',
        icon: 'Folder',
        path: '/documents/library',
        permissions: ['document:read'],
      },
      {
        id: 'validation',
        label: 'Validation Results',
        icon: 'Gavel',
        path: '/documents/validation',
        permissions: ['document:read'],
      },
    ],
  },
  {
    id: 'validation',
    label: 'Validation',
    icon: 'Assessment',
    path: '/validation',
    permissions: ['validation:read'],
    children: [
      {
        id: 'rules',
        label: 'Validation Rules',
        icon: 'Gavel',
        path: '/validation/rules',
        permissions: ['validation:write'],
      },
      {
        id: 'analytics',
        label: 'Validation Analytics',
        icon: 'Analytics',
        path: '/validation/analytics',
        permissions: ['validation:read'],
      },
    ],
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: 'Analytics',
    path: '/reports',
    permissions: ['report:read'],
    children: [
      {
        id: 'compliance',
        label: 'Compliance Reports',
        icon: 'Assessment',
        path: '/reports/compliance',
        permissions: ['report:read'],
      },
      {
        id: 'audit',
        label: 'Audit Trail',
        icon: 'History',
        path: '/reports/audit',
        permissions: ['audit:read'],
      },
      {
        id: 'analytics',
        label: 'Analytics',
        icon: 'Analytics',
        path: '/reports/analytics',
        permissions: ['analytics:read'],
      },
    ],
  },
  {
    id: 'admin',
    label: 'Administration',
    icon: 'Settings',
    path: '/admin',
    permissions: ['system:write'],
    children: [
      {
        id: 'users',
        label: 'User Management',
        icon: 'People',
        path: '/admin/users',
        permissions: ['user:write'],
      },
      {
        id: 'companies',
        label: 'Company Management',
        icon: 'Business',
        path: '/admin/companies',
        permissions: ['company:write'],
      },
      {
        id: 'settings',
        label: 'System Settings',
        icon: 'Settings',
        path: '/admin/settings',
        permissions: ['system:write'],
      },
      {
        id: 'security',
        label: 'Security',
        icon: 'Security',
        path: '/admin/security',
        permissions: ['security:read'],
      },
    ],
  },
];

const iconMap: { [key: string]: React.ElementType } = {
  Dashboard: DashboardIcon,
  UploadFile: UploadFile,
  Folder: Folder,
  Description: Description,
  Assessment: Assessment,
  Gavel: Gavel,
  Analytics: Analytics,
  History: History,
  Settings: Settings,
  People: People,
  Business: Business,
  Security: Security,
};

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, width = 280 }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { hasPermission } = usePermissions();
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['documents', 'validation']);

  const handleNavigation = (path: string) => {
    navigate(path);
    onClose();
  };

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isItemActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const renderNavigationItem = (item: NavigationItem, depth: number = 0) => {
    const Icon = iconMap[item.icon];
    const hasChildren = item.children && item.children.length > 0;
    const isActive = isItemActive(item.path);
    const isExpanded = expandedItems.includes(item.id);

    if (!hasPermission(...(item.permissions || []))) {
      return null;
    }

    return (
      <React.Fragment key={item.id}>
        <ListItem disablePadding>
          <ListItemButton
            selected={isActive}
            onClick={() => {
              if (hasChildren) {
                toggleExpanded(item.id);
              } else {
                handleNavigation(item.path);
              }
            }}
            sx={{
              pl: 2 + depth * 2,
              minHeight: 48,
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              <Icon color={isActive ? 'primary' : 'inherit'} />
            </ListItemIcon>
            <ListItemText
              primary={item.label}
              primaryTypographyProps={{
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'primary.main' : 'inherit',
              }}
            />
            {hasChildren && (
              isExpanded ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
        </ListItem>

        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, depth + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <Drawer
      variant="temporary"
      anchor="left"
      open={open}
      onClose={onClose}
      ModalProps={{
        keepMounted: true, // Better open performance on mobile.
      }}
      sx={{
        width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
        },
      }}
    >
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Logo/Brand */}
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
            LegalDoc AI
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Document Automation
          </Typography>
        </Box>

        {/* Navigation */}
        <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
          <List component="nav" sx={{ px: 1, py: 1 }}>
            {navigationItems.map(item => renderNavigationItem(item))}
          </List>
        </Box>

        {/* Footer */}
        <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
          <Typography variant="caption" color="text.secondary" align="center">
            Version 1.0.0
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar;