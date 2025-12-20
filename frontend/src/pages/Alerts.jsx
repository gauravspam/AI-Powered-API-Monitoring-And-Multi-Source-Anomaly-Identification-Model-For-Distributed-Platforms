import { alertsData } from "../data/dummyData";
import { Typography, Paper } from "@mui/material";

const Alerts = () => {
  return (
    <>
      <Typography variant="h4" gutterBottom>Alerts</Typography>

      {alertsData.map((a, i) => (
        <Paper key={i} sx={{ p: 2, mb: 1 }}>
          {a.name} | {a.api} | {a.severity} | {a.status}
        </Paper>
      ))}
    </>
  );
};

export default Alerts;
