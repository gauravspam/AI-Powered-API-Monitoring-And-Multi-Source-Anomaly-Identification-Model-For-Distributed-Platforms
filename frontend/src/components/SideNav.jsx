import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import {
  Insights as InsightsIcon,
  Http as HttpIcon,
  NotificationsActive as NotificationsActiveIcon,
  Article as ArticleIcon,
  AutoGraph as AutoGraphIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const navItems = [
  { label: 'Dashboard', path: '/', icon: <InsightsIcon /> },
  { label: 'Services', path: '/services', icon: <HttpIcon /> },
  { label: 'Alerts', path: '/alerts', icon: <NotificationsActiveIcon /> },
  { label: 'Logs', path: '/logs', icon: <ArticleIcon /> },
  { label: 'Models', path: '/models', icon: <AutoGraphIcon /> },
  { label: 'Settings', path: '/settings', icon: <SettingsIcon /> },
];

export const SideNav = ({ drawerWidth, mobileOpen, onDrawerToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const drawer = (
    <div>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <AutoGraphIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" noWrap>
            API Monitor
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List>
        {navItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => {
              navigate(item.path);
              if (mobileOpen) onDrawerToggle();
            }}
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                color: location.pathname === item.path ? 'inherit' : 'text.primary',
              }}
            >
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </div>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
    >
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
        }}
      >
        {drawer}
      </Drawer>
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
        }}
        open
      >
        {drawer}
      </Drawer>
    </Box>
  );
};

export default SideNav;
