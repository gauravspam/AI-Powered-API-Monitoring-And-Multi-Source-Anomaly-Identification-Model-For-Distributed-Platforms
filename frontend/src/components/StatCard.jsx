import { Paper, Typography, Box, useTheme } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

export const StatCard = ({ label, value, unit, trend, trendDirection, icon: Icon }) => {
  const theme = useTheme();
  const TrendIcon = trendDirection === 'up' ? TrendingUp : TrendingDown;
  const trendColor =
    trendDirection === 'up'
      ? theme.palette.success.main
      : theme.palette.error.main;

  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {Icon && (
        <Box
          sx={{
            position: 'absolute',
            right: -4,
            top: -4,
            opacity: 0.1,
          }}
        >
          <Icon sx={{ fontSize: 80 }} />
        </Box>
      )}
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {label}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
        <Typography variant="h4" component="div" fontWeight="bold">
          {value}
        </Typography>
        {unit && (
          <Typography variant="body1" color="text.secondary" sx={{ ml: 0.5 }}>
            {unit}
          </Typography>
        )}
      </Box>
      {trend !== undefined && (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TrendIcon sx={{ fontSize: 20, color: trendColor }} />
          <Typography
            variant="body2"
            sx={{ color: trendColor, fontWeight: 500, ml: 0.5 }}
          >
            {trend}%
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            vs last hour
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default StatCard;
