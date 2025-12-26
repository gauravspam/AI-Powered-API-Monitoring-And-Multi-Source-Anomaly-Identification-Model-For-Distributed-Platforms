import { Container, Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { SentimentDissatisfied } from '@mui/icons-material';

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
        }}
      >
        <SentimentDissatisfied sx={{ fontSize: 100, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h3" gutterBottom fontWeight="bold">
          404
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Page Not Found
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          The page you're looking for doesn't exist or has been moved.
        </Typography>
        <Button variant="contained" size="large" onClick={() => navigate('/')}>
          Go to Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound;
