import {
  AppBar,Toolbar,
  Typography,IconButton,
  Menu,MenuItem,
  Badge,Box,Avatar
} from "@mui/material";

import NotificationsIcon from "@mui/icons-material/Notifications";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";

import { useContext, useState } from "react";
import { ColorModeContext } from "../theme/ThemeContext";
import { useTheme } from "@mui/material/styles";

const TopNavbar = () => {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  // Notification menu
  const [notifAnchor, setNotifAnchor] = useState(null);
  const openNotif = Boolean(notifAnchor);

  // User menu
  const [userAnchor, setUserAnchor] = useState(null);
  const openUser = Boolean(userAnchor);

  const dummyNotifications = [
    "High latency detected in Order API",
    "New anomaly detected in Auth API",
    "Prediction risk increased"
  ];

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Typography variant="h6">
          AI API Monitoring
        </Typography>

        <Box>
          {/* Notifications */}
          <IconButton onClick={(e) => setNotifAnchor(e.currentTarget)}>
            <Badge badgeContent={dummyNotifications.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          <Menu
            anchorEl={notifAnchor}
            open={openNotif}
            onClose={() => setNotifAnchor(null)}
          >
            {dummyNotifications.map((n, i) => (
              <MenuItem key={i}>{n}</MenuItem>
            ))}
          </Menu>

          {/* Theme Toggle */}
          <IconButton onClick={colorMode.toggleColorMode}>
            {theme.palette.mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>

          {/* User Profile */}
          <IconButton onClick={(e) => setUserAnchor(e.currentTarget)}>
            <Avatar sx={{ width: 32, height: 32 }}>S</Avatar>
          </IconButton>

          <Menu
            anchorEl={userAnchor}
            open={openUser}
            onClose={() => setUserAnchor(null)}
          >
            <MenuItem disabled>👤 Sujal (Dummy)</MenuItem>
            <MenuItem>Profile</MenuItem>
            <MenuItem>Logout</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TopNavbar;
