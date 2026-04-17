import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 2 }}>
      <Typography variant="h4" sx={{ fontWeight: 700, color: 'text.secondary' }}>404</Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>Page not found</Typography>
      <Button variant="outlined" startIcon={<Home size={14} />} onClick={() => navigate('/')}>
        Back to Overview
      </Button>
    </Box>
  );
}
