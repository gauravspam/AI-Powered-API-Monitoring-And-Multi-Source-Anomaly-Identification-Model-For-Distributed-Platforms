import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const Models = () => {
    return (
        <Container maxWidth="xl">
            <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }}>ML Models</Typography>
            <Paper sx={{ p: 3 }}>
                <Typography variant="h6">Active Model: Fusion_V2</Typography>
                <Box sx={{ mt: 2 }}>
                    <Typography>Type: Multi-Modal Fusion (Log + Metric + Trace)</Typography>
                    <Typography>Status: <span style={{ color: 'green' }}>Active</span></Typography>
                    <Typography>Last Training: 2025-02-10</Typography>
                </Box>
            </Paper>
        </Container>
    );
};

export default Models;
