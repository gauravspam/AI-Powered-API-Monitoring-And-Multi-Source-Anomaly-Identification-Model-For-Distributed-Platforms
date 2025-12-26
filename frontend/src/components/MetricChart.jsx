import { LineChart } from '@mui/x-charts/LineChart';
import { Paper, Typography } from '@mui/material';

export const MetricChart = ({ data, metricKey, title, height = 300 }) => {
  // Transform data for MUI X Charts
  const xData = data.map((d) => new Date(d.timestamp));
  const yData = data.map((d) => d[metricKey]);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <LineChart
        xAxis={[{
          data: xData,
          scaleType: 'time',
          valueFormatter: (date) => date.toLocaleTimeString(),
        }]}
        series={[
          {
            data: yData,
            label: title,
            color: '#42a5f5',
            curve: 'catmullRom',
          },
        ]}
        height={height}
        margin={{ left: 70, right: 20, top: 20, bottom: 30 }}
        grid={{ vertical: true, horizontal: true }}
      />
    </Paper>
  );
};

export default MetricChart;
