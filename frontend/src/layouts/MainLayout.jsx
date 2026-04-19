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
  useTheme,
  Badge,
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
  ChevronLeft,
  ChevronRight,
  Activity,
  Wifi,
} from 'lucide-react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useThemeMode } from '@/context/ThemeContext';
import { useQuery } from '@tanstack/react-query';
import { BACKEND_URL } from '@/api/http';

const DRAWER_WIDE = 220;
const DRAWER_SLIM = 56;

const NAV_ITEMS = [
  { path: '/',          label: 'Overview',   icon: LayoutDashboard },
  { path: '/services',  label: 'Services',   icon: Server },
  { path: '/alerts',    label: 'Alerts',     icon: Bell, badge: true },
  { path: '/logs',      label: 'Logs',       icon: FileText },
  { path: '/traces',    label: 'Traces',     icon: GitBranch },
  { path: '/models',    label: 'ML Models',  icon: Cpu },
  { path: '/simulator', label: 'Simulator',  icon: Zap },
];

// Lightweight active anomaly count for sidebar badge
const useActiveBadge = () =>
  useQuery({
    queryKey: ['/api/sidebar/badge'],
    queryFn: async () => {
      try {
        const r = await fetch(`${BACKEND_URL}/api/anomalies?limit=100`, {
          signal: AbortSignal.timeout(4000),
        });
        if (!r.ok) throw new Error();
        const d = await r.json();
        const list = Array.isArray(d) ? d : [];
        return list.filter((a) => a.status === 'ACTIVE').length;
      } catch {
        return 0;
      }
    },
    refetchInterval: 20000,
    staleTime: 15000,
  });

export const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const { isDark, toggleTheme } = useThemeMode();
  const navigate   = useNavigate();
  const location   = useLocation();
  const theme      = useTheme();
  const { data: activeBadge = 0 } = useActiveBadge();

  // Live clock
  const [clock, setClock] = useState(() => new Date().toLocaleTimeString());
  useEffect(() => {
    const id = setInterval(() => setClock(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(id);
  }, []);

  const drawerWidth = collapsed ? DRAWER_SLIM : DRAWER_WIDE;

  const currentLabel =
    NAV_ITEMS.find(
      (n) => n.path === location.pathname ||
             (n.path !== '/' && location.pathname.startsWith(n.path))
    )?.label || 'Overview';

  const sidebarBg = theme.palette.mode === 'dark'
    ? 'hsl(222, 22%, 7%)'
    : theme.palette.background.default;

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* ── Sidebar ── */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          transition: 'width 0.2s',
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            borderRight: '1px solid',
            borderColor: 'divider',
            backgroundColor: sidebarBg,
            transition: 'width 0.2s',
            overflowX: 'hidden',
            overscrollBehavior: 'contain',
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

          {/* ── Logo ── */}
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            p: collapsed ? 1.5 : 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            minHeight: 52,
            justifyContent: collapsed ? 'center' : 'flex-start',
          }}>
            <Box sx={{ flexShrink: 0 }}>
              <svg width="26" height="26" viewBox="0 0 28 28" fill="none" aria-label="AnomalyIQ">
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
              <Box sx={{ flex: 1, overflow: 'hidden' }}>
                <Typography variant="caption" sx={{
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  lineHeight: 1.1,
                  display: 'block',
                  color: 'text.primary',
                  whiteSpace: 'nowrap',
                }}>
                  AnomalyIQ
                </Typography>
                <Typography variant="caption" sx={{
                  fontSize: '0.6rem',
                  color: 'text.secondary',
                  lineHeight: 1,
                  display: 'block',
                  whiteSpace: 'nowrap',
                }}>
                  SRE Monitor
                </Typography>
              </Box>
            )}

            <Tooltip title={collapsed ? 'Expand' : 'Collapse'} placement="right" arrow>
              <IconButton
                size="small"
                onClick={() => setCollapsed((c) => !c)}
                sx={{ ml: collapsed ? 0 : 'auto', color: 'text.secondary', flexShrink: 0 }}
              >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
              </IconButton>
            </Tooltip>
          </Box>

          {/* ── Nav ── */}
          <List sx={{ flex: 1, py: 1, px: 0.5 }}>
            {NAV_ITEMS.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path));
              const Icon = item.icon;
              const badgeCount = item.badge ? activeBadge : 0;

              return (
                <ListItemButton
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  sx={{
                    mx: 0.5,
                    my: 0.25,
                    borderRadius: 1.5,
                    px: 1.5,
                    py: 0.875,
                    backgroundColor: isActive ? 'action.selected' : 'transparent',
                    borderLeft: isActive ? '2px solid' : '2px solid transparent',
                    borderColor: isActive ? 'primary.main' : 'transparent',
                    '&:hover': { backgroundColor: 'action.hover' },
                    justifyContent: collapsed ? 'center' : 'flex-start',
                    minHeight: 38,
                    transition: 'all 0.15s',
                  }}
                >
                  <Tooltip title={collapsed ? item.label : ''} placement="right" arrow>
                    <ListItemIcon sx={{
                      minWidth: collapsed ? 0 : 30,
                      color: isActive ? 'primary.main' : 'text.secondary',
                    }}>
                      {badgeCount > 0 ? (
                        <Badge
                          badgeContent={badgeCount}
                          color="error"
                          sx={{
                            '& .MuiBadge-badge': {
                              fontSize: '0.55rem',
                              minWidth: 14,
                              height: 14,
                              right: -4,
                              top: -2,
                            },
                          }}
                        >
                          <Icon size={15} />
                        </Badge>
                      ) : (
                        <Icon size={15} />
                      )}
                    </ListItemIcon>
                  </Tooltip>
                  {!collapsed && (
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.8125rem',
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? 'text.primary' : 'text.secondary',
                      }}
                    />
                  )}
                </ListItemButton>
              );
            })}
          </List>

          {/* ── Bottom: theme toggle ── */}
          <Box sx={{ borderTop: '1px solid', borderColor: 'divider', p: 0.5 }}>
            <Tooltip title={isDark ? 'Light mode' : 'Dark mode'} placement="right" arrow>
              <ListItemButton
                onClick={toggleTheme}
                sx={{
                  borderRadius: 1.5,
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  py: 1,
                  px: 1.5,
                }}
              >
                <ListItemIcon sx={{ minWidth: collapsed ? 0 : 30, color: 'text.secondary' }}>
                  {isDark ? <Sun size={15} /> : <Moon size={15} />}
                </ListItemIcon>
                {!collapsed && (
                  <ListItemText
                    primary={isDark ? 'Light Mode' : 'Dark Mode'}
                    primaryTypographyProps={{ fontSize: '0.8125rem', color: 'text.secondary' }}
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
        <Box sx={{
          minHeight: 50,
          borderBottom: '1px solid',
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2.5,
          flexShrink: 0,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Activity size={14} style={{ color: 'hsl(188, 80%, 42%)' }} />
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
              {currentLabel}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Live indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Box sx={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                backgroundColor: 'success.main',
                animation: 'livePulse 2s ease-in-out infinite',
                '@keyframes livePulse': {
                  '0%, 100%': { opacity: 1, transform: 'scale(1)' },
                  '50%': { opacity: 0.5, transform: 'scale(0.85)' },
                },
              }} />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>
                Live
              </Typography>
            </Box>

            {/* Clock */}
            <Typography variant="caption" sx={{
              color: 'text.secondary',
              fontVariantNumeric: 'tabular-nums',
              fontFamily: 'monospace',
              fontSize: '0.75rem',
            }}>
              {clock}
            </Typography>

            {/* Theme toggle quick access */}
            <Tooltip title={isDark ? 'Switch to light' : 'Switch to dark'} arrow>
              <IconButton
                size="small"
                onClick={toggleTheme}
                sx={{ color: 'text.secondary', p: 0.5 }}
              >
                {isDark ? <Sun size={14} /> : <Moon size={14} />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Page content */}
        <Box sx={{
          flex: 1,
          overflow: 'auto',
          p: 2.5,
          overscrollBehavior: 'contain',
        }}>
          {children ?? <Outlet />}
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;
