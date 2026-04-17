import { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  LayoutDashboard,
  Server,
  Bell,
  FileText,
  GitBranch,
  Cpu,
  Zap,
  Moon,
  Sun,
  ChevronRight,
  ChevronLeft,
  Menu,
} from 'lucide-react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';

const drawerWidth = 220;

const navItems = [
  { path: '/', label: 'Overview', icon: <LayoutDashboard size={15} /> },
  { path: '/services', label: 'Services', icon: <Server size={15} /> },
  { path: '/alerts', label: 'Alerts', icon: <Bell size={15} /> },
  { path: '/logs', label: 'Logs', icon: <FileText size={15} /> },
  { path: '/traces', label: 'Traces', icon: <GitBranch size={15} /> },
  { path: '/models', label: 'ML Models', icon: <Cpu size={15} /> },
  { path: '/simulator', label: 'Simulator', icon: <Zap size={15} /> },
];

/**
 * MainLayout — permanent sidebar + top bar + main content area.
 *
 * Supports two usage modes:
 *   1. <MainLayout>  →  renders <Outlet /> (React Router nested routes)
 *   2. <MainLayout>{children}</MainLayout>  →  renders children prop (legacy)
 */
export const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Theme toggle (adds/removes 'light' class on <html>)
  useEffect(() => {
    if (!dark) {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }, [dark]);

  // Live clock in top bar
  useEffect(() => {
    const el = document.getElementById('topbar-time');
    const interval = setInterval(() => {
      if (el) el.textContent = new Date().toLocaleTimeString();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const width = collapsed ? 56 : drawerWidth;
  const currentLabel =
    navItems.find(
      (n) =>
        n.path === location.pathname ||
        (n.path !== '/' && location.pathname.startsWith(n.path))
    )?.label || 'Overview';

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* ── Sidebar ── */}
      <Drawer
        variant="permanent"
        sx={{
          width,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width,
            boxSizing: 'border-box',
            borderRight: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'hsl(222, 22%, 7%)',
            transition: 'width 0.2s',
            overflowX: 'hidden',
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Logo */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              p: 2,
              borderBottom: '1px solid',
              borderColor: 'divider',
              minHeight: 52,
            }}
          >
            <Box sx={{ flexShrink: 0 }}>
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-label="Anomaly Monitor">
                <rect width="28" height="28" rx="6" fill="hsl(188, 80%, 42%)" opacity="0.15" />
                <path
                  d="M4 20 L9 12 L14 16 L18 8 L24 20"
                  stroke="hsl(188, 80%, 42%)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                />
                <circle cx="18" cy="8" r="2.5" fill="hsl(188, 80%, 42%)" />
                <circle cx="9" cy="12" r="1.5" fill="hsl(188, 80%, 42%)" opacity="0.6" />
              </svg>
            </Box>

            {!collapsed && (
              <Box sx={{ overflow: 'hidden' }}>
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    lineHeight: 1,
                    display: 'block',
                    color: 'text.primary',
                    whiteSpace: 'nowrap',
                  }}
                >
                  AnomalyIQ
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    color: 'text.secondary',
                    lineHeight: 1,
                    mt: 0.5,
                    display: 'block',
                    whiteSpace: 'nowrap',
                  }}
                >
                  API Monitor
                </Typography>
              </Box>
            )}

            <Tooltip title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} arrow>
              <IconButton
                size="small"
                onClick={() => setCollapsed(!collapsed)}
                sx={{ ml: 'auto', color: 'text.secondary', flexShrink: 0 }}
              >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={16} />}
              </IconButton>
            </Tooltip>
          </Box>

          {/* Nav items */}
          <List sx={{ flex: 1, py: 1 }}>
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <ListItemButton
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  sx={{
                    mx: 1,
                    my: 0.25,
                    borderRadius: 1,
                    px: 1.5,
                    py: 1,
                    backgroundColor: isActive ? 'action.selected' : 'transparent',
                    '&:hover': { backgroundColor: 'action.hover' },
                    justifyContent: collapsed ? 'center' : 'flex-start',
                    minHeight: 40,
                  }}
                >
                  <Tooltip title={collapsed ? item.label : ''} placement="right" arrow>
                    <ListItemIcon
                      sx={{
                        minWidth: collapsed ? 0 : 32,
                        color: isActive ? 'primary.main' : 'text.primary',
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                  </Tooltip>
                  {!collapsed && (
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.875rem',
                        fontWeight: isActive ? 500 : 400,
                      }}
                    />
                  )}
                  {!collapsed && item.path === '/alerts' && (
                    <Box
                      sx={{
                        ml: 'auto',
                        px: 0.5,
                        py: 0.25,
                        borderRadius: 0.5,
                        backgroundColor: 'error.main',
                        fontSize: '0.625rem',
                        fontWeight: 600,
                        color: 'white',
                        lineHeight: 1.4,
                      }}
                    >
                      5
                    </Box>
                  )}
                </ListItemButton>
              );
            })}
          </List>

          {/* Bottom: theme toggle */}
          <Box sx={{ borderTop: '1px solid', borderColor: 'divider', p: 1 }}>
            <Tooltip title={dark ? 'Switch to light mode' : 'Switch to dark mode'} placement="right" arrow>
              <ListItemButton
                onClick={() => setDark(!dark)}
                sx={{
                  borderRadius: 1,
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  py: 1,
                }}
              >
                <ListItemIcon sx={{ minWidth: collapsed ? 0 : 32, color: 'text.secondary' }}>
                  {dark ? <Sun size={16} /> : <Moon size={16} />}
                </ListItemIcon>
                {!collapsed && (
                  <ListItemText
                    primary={dark ? 'Light Mode' : 'Dark Mode'}
                    primaryTypographyProps={{ fontSize: '0.875rem' }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          </Box>
        </Box>
      </Drawer>

      {/* ── Main content ── */}
      <Box
        component="main"
        sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}
      >
        {/* Top bar */}
        <Box
          sx={{
            minHeight: 52,
            borderBottom: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
            {currentLabel}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                fontSize: '0.75rem',
                color: 'text.secondary',
              }}
            >
              <Box
                component="span"
                sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'success.main' }}
              />
              <span>Live</span>
            </Box>
            <Typography
              variant="caption"
              sx={{ color: 'text.secondary', fontVariantNumeric: 'tabular-nums' }}
              id="topbar-time"
            >
              {new Date().toLocaleTimeString()}
            </Typography>
          </Box>
        </Box>

        {/* Page content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2.5 }}>
          {/* Support both <Outlet /> (nested routes) and children prop */}
          {children ?? <Outlet />}
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;
