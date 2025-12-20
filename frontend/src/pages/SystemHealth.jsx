import { systemHealthData } from "../data/dummyData";
import { Typography, Paper } from "@mui/material";

const SystemHealth = () => {
  return (
    <>
      <Typography variant="h4" gutterBottom>System Health</Typography>

      {Object.entries(systemHealthData).map(([key, value]) => (
        <Paper key={key} sx={{ p: 2, mb: 1 }}>
          {key.toUpperCase()} : {value}
        </Paper>
      ))}
    </>
  );
};

export default SystemHealth;
