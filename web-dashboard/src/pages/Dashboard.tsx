import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
} from '@mui/material';
import {
  Description,
  CloudUpload,
  Security,
  Assessment,
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Info,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, Area, AreaChart } from 'recharts';

import { DashboardStats } from '@/types';
import documentService from '@/services/documentService';
import validationService from '@/services/validationService';
import apiService from '@/services/api';

const Dashboard: React.FC = () => {
  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboard-stats',
    async () => {
      const response = await apiService.get('/dashboard/stats');
      return response.data;
    },
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  // Fetch validation statistics
  const { data: validationStats } = useQuery(
    'validation-stats',
    () => validationService.getValidationStats(),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  // Fetch recent activity
  const { data: recentActivity } = useQuery(
    'recent-activity',
    async () => {
      const response = await apiService.get('/dashboard/activity');
      return response.data;
    },
    {
      refetchInterval: 30000,
    }
  );

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#9e9e9e';
    }
  };

  const getOutcomeIcon = (outcome: string) => {
    switch (outcome) {
      case 'success': return <CheckCircle color="success" />;
      case 'failure': return <ErrorIcon color="error" />;
      default: return <Info color="info" />;
    }
  };

  if (statsLoading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  // Prepare chart data
  const validationChartData = stats?.validationStats ? [
    { name: 'Compliant', value: stats.validationStats.compliant, color: '#4caf50' },
    { name: 'Non-Compliant', value: stats.validationStats.nonCompliant, color: '#f44336' },
    { name: 'Pending', value: stats.validationStats.pending, color: '#ff9800' },
  ] : [];

  const riskChartData = stats?.riskStats ? [
    { name: 'Low', value: stats.riskStats.low, color: '#4caf50' },
    { name: 'Medium', value: stats.riskStats.medium, color: '#ff9800' },
    { name: 'High', value: stats.riskStats.high, color: '#f44336' },
    { name: 'Critical', value: stats.riskStats.critical, color: '#d32f2f' },
  ] : [];

  const activityTrendData = recentActivity?.activityTrend || [];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Welcome to your legal document automation dashboard
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Description sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h4" component="div">
                  {stats?.totalDocuments || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Documents
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  +{stats?.documentsToday || 0} today
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CloudUpload sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h4" component="div">
                  {stats?.validationStats?.total || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Validations Today
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {stats?.validationStats?.compliant || 0} compliant
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Security sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h4" component="div">
                  {stats?.securityAlerts?.length || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Security Alerts
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {stats?.securityAlerts && stats.securityAlerts.length > 0 ? (
                  <Warning sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                ) : (
                  <CheckCircle sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                )}
                <Typography variant="caption" color={stats?.securityAlerts?.length > 0 ? 'warning.main' : 'success.main'}>
                  {stats?.securityAlerts?.length > 0 ? 'Needs attention' : 'All clear'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Assessment sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h4" component="div">
                  {stats?.activeUsers || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Active Users
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  of {stats?.totalUsers || 0} total
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Activity */}
      <Grid container spacing={3}>
        {/* Validation Status Chart */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Validation Status
            </Typography>
            {validationChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={validationChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {validationChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 220 }}>
                <Typography variant="body2" color="text.secondary">
                  No validation data available
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Risk Assessment Chart */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Risk Assessment
            </Typography>
            {riskChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={riskChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8">
                    {riskChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 220 }}>
                <Typography variant="body2" color="text.secondary">
                  No risk data available
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List sx={{ maxHeight: 220, overflow: 'auto' }}>
              {stats?.recentActivity?.slice(0, 5).map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {getOutcomeIcon(activity.outcome)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.description}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {activity.userName} • {activity.companyName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(activity.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < 4 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
              {(!stats?.recentActivity || stats.recentActivity.length === 0) && (
                <ListItem>
                  <ListItemText
                    primary="No recent activity"
                    secondary="Activity will appear here once users start using the system"
                  />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Security Alerts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Security Alerts
            </Typography>
            <List>
              {stats?.securityAlerts?.map((alert, index) => (
                <React.Fragment key={alert.id}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Avatar sx={{ bgcolor: getSeverityColor(alert.severity), width: 32, height: 32 }}>
                        <Warning sx={{ fontSize: 18 }} />
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={alert.description}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={alert.severity}
                            size="small"
                            sx={{
                              backgroundColor: getSeverityColor(alert.severity),
                              color: 'white',
                              fontSize: '0.7rem',
                              height: 20,
                            }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {new Date(alert.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < (stats?.securityAlerts?.length || 0) - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
              {(!stats?.securityAlerts || stats.securityAlerts.length === 0) && (
                <ListItem>
                  <ListItemText
                    primary="No security alerts"
                    secondary="All systems operating normally"
                    primaryTypographyProps={{ color: 'success.main' }}
                  />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Activity Trend */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Activity Trend (Last 7 Days)
            </Typography>
            {activityTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={activityTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="documents"
                    stackId="1"
                    stroke="#8884d8"
                    fill="#8884d8"
                    name="Documents"
                  />
                  <Area
                    type="monotone"
                    dataKey="validations"
                    stackId="1"
                    stroke="#82ca9d"
                    fill="#82ca9d"
                    name="Validations"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 250 }}>
                <Typography variant="body2" color="text.secondary">
                  No trend data available
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;