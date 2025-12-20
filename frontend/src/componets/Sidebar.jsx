import { Drawer, List, ListItem, ListItemIcon, ListItemText } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ApiIcon from "@mui/icons-material/Api";
import WarningIcon from "@mui/icons-material/Warning";
import TimelineIcon from "@mui/icons-material/Timeline";
import NotificationsIcon from "@mui/icons-material/Notifications";
import StorageIcon from "@mui/icons-material/Storage";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import { useNavigate } from "react-router-dom";

const Sidebar = () => {
  const navigate = useNavigate();

  return (
    <Drawer variant="permanent" sx={{ width: 240 }}>
      <List>
        <ListItem button onClick={() => navigate("/")}>
          <ListItemIcon><DashboardIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>

        <ListItem button onClick={() => navigate("/apis")}>
          <ListItemIcon><ApiIcon /></ListItemIcon>
          <ListItemText primary="APIs" />
        </ListItem>

        <ListItem button onClick={() => navigate("/anomalies")}>
          <ListItemIcon><WarningIcon /></ListItemIcon>
          <ListItemText primary="Anomalies" />
        </ListItem>

        <ListItem button onClick={() => navigate("/predictions")}>
          <ListItemIcon><TimelineIcon /></ListItemIcon>
          <ListItemText primary="Predictions" />
        </ListItem>

        <ListItem button onClick={() => navigate("/alerts")}>
          <ListItemIcon><NotificationsIcon /></ListItemIcon>
          <ListItemText primary="Alerts" />
        </ListItem>

        <ListItem button onClick={() => navigate("/logs")}>
          <ListItemIcon><StorageIcon /></ListItemIcon>
          <ListItemText primary="Logs Explorer" />
        </ListItem>

        <ListItem button onClick={() => navigate("/system-health")}>
          <ListItemIcon><HealthAndSafetyIcon /></ListItemIcon>
          <ListItemText primary="System Health" />
        </ListItem>
      </List>
    </Drawer>
  );
};

export default Sidebar;
