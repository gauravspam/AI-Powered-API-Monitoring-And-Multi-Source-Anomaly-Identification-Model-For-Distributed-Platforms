import { dashboardData } from "../data/dummyData.js";
import { Typography, Grid, Paper } from "@mui/material";

const Dashboard = () => {
  const { kpis, recentAnomalies } = dashboardData;

  return (
    <>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>

      <Grid container spacing={2}>
        {Object.entries(kpis).map(([key, value]) => (
          <Grid item xs={12} md={2} key={key}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2">{key.toUpperCase()}</Typography>
              <Typography variant="h6">{value}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h6" sx={{ mt: 4 }}>Recent Anomalies</Typography>
      {recentAnomalies.map((a, i) => (
        <Paper key={i} sx={{ p: 2, mt: 1 }}>
          {a.api} – {a.type} – {a.severity}
        </Paper>
      ))}
    </>
  );
};

export default Dashboard;
