import { predictionsData } from "../data/dummyData";
import { Typography, Paper } from "@mui/material";

const Predictions = () => {
  return (
    <>
      <Typography variant="h4" gutterBottom>Predictions</Typography>

      {predictionsData.map((p, i) => (
        <Paper key={i} sx={{ p: 2, mb: 1 }}>
          {p.api} → Risk: {p.risk} | ETA: {p.eta}
        </Paper>
      ))}
    </>
  );
};

export default Predictions;
