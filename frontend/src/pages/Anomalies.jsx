import { anomaliesData } from "../data/dummyData";
import { Typography, Paper } from "@mui/material";

const Anomalies = () => {
  return (
    <>
      <Typography variant="h4" gutterBottom>Anomalies</Typography>

      {anomaliesData.map((a, i) => (
        <Paper key={i} sx={{ p: 2, mb: 1 }}>
          {a.api} | {a.type} | Score: {a.score} | {a.severity}
        </Paper>
      ))}
    </>
  );
};

export default Anomalies;
