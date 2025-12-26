import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  InputBase,
  Avatar,
  Menu,
  MenuItem,
  Box,
  useTheme,
} from '@mui/material';

  
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { useState, useContext } from 'react';
import { ThemeContext } from '@/App';

export const TopBar = ({ drawerWidth, onMenuClick }) => {
  const theme = useTheme();
  const { toggleTheme } = useContext(ThemeContext);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { sm: `calc(100% - ${drawerWidth}px)` },
        ml: { sm: `${drawerWidth}px` },
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
        
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 0, mr: 3 }}>
          AI Anomaly Monitor
        </Typography>

        <Box
          sx={{
            position: 'relative',
            borderRadius: 1,
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.25)',
            },
            marginRight: 2,
            marginLeft: 0,
            width: '100%',
            maxWidth: '400px',
          }}
        >
          <Box
            sx={{
              padding: theme.spacing(0, 2),
              height: '100%',
              position: 'absolute',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SearchIcon />
          </Box>
          <InputBase
            placeholder="Search services, logs, alerts..."
            sx={{
              color: 'inherit',
              width: '100%',
              '& .MuiInputBase-input': {
                padding: theme.spacing(1, 1, 1, 0),
                paddingLeft: `calc(1em + ${theme.spacing(4)})`,
                transition: theme.transitions.create('width'),
                width: '100%',
              },
            }}
          />
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <IconButton color="inherit" onClick={toggleTheme}>
          {theme.palette.mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
        </IconButton>

        <IconButton
          edge="end"
          onClick={handleMenuOpen}
          color="inherit"
        >
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>A</Avatar>
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>Profile</MenuItem>
          <MenuItem onClick={handleMenuClose}>Settings</MenuItem>
          <MenuItem onClick={handleMenuClose}>Logout</MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;
