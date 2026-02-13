import React, { useState } from 'react';
import {
    Container, Paper, Typography, Box, Button, Grid, // Ensure this imports Grid v2 or Grid
    CircularProgress, Alert, Card, CardContent, Divider
} from '@mui/material';
import {
    Psychology as BrainIcon,
    CheckCircle as HealthyIcon,
    Warning as AnomalyIcon
} from '@mui/icons-material';
import api from '../api/http';

const MLSimulator = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const generatePayload = (isAnomaly) => {
        const now = new Date();
        return {
            apiName: isAnomaly ? "simulated-attack-node" : "healthy-node",
            timestamp: now.toISOString(),
            cpuUsage: isAnomaly ? 95.5 : 15.2,
            memoryUsage: isAnomaly ? 88.0 : 42.1,
            logMessage: isAnomaly ? "CRITICAL: Buffer Overflow Detected" : "Health check passed",
            logLevel: isAnomaly ? "ERROR" : "INFO"
        };
    };

    const handlePredict = async (simulateAnomaly) => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // Use the correct endpoint you verified works
            const response = await api.post('/test-ml/trigger', generatePayload(simulateAnomaly));
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.message || "Failed to connect to ML Service");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
                <BrainIcon fontSize="large" color="primary" />
                <Typography variant="h4" fontWeight="bold">ML Anomaly Simulator</Typography>
            </Box>

            {/* MUI v6/v7 Grid Syntax Fix */}
            <Grid container spacing={3}>
                {/* Control Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3, height: '100%' }}>
                        <Typography variant="h6" gutterBottom>Simulation Controls</Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            Generate synthetic telemetry data and send it to the Multi-Source AI model for analysis.
                        </Typography>

                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 3 }}>
                            <Button
                                variant="contained"
                                color="success"
                                size="large"
                                onClick={() => handlePredict(false)}
                                disabled={loading}
                                startIcon={<HealthyIcon />}
                            >
                                SIMULATE NORMAL TRAFFIC
                            </Button>

                            <Button
                                variant="contained"
                                color="error"
                                size="large"
                                onClick={() => handlePredict(true)}
                                disabled={loading}
                                startIcon={<AnomalyIcon />}
                            >
                                SIMULATE ATTACK / ANOMALY
                            </Button>
                        </Box>

                        {loading && (
                            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                                <CircularProgress />
                            </Box>
                        )}

                        {error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}
                    </Paper>
                </Grid>

                {/* Results Panel */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 3, minHeight: 400, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                        {!result ? (
                            <Box sx={{ textAlign: 'center', opacity: 0.5 }}>
                                <BrainIcon sx={{ fontSize: 60, mb: 2 }} />
                                <Typography>Ready to analyze. Waiting for data...</Typography>
                            </Box>
                        ) : (
                            <Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                    {result.result?.is_anomaly ? (
                                        <AnomalyIcon color="error" sx={{ fontSize: 40 }} />
                                    ) : (
                                        <HealthyIcon color="success" sx={{ fontSize: 40 }} />
                                    )}
                                    <Box>
                                        <Typography variant="overline" color="text.secondary">DIAGNOSIS</Typography>
                                        <Typography variant="h4" color={result.result?.is_anomaly ? "error.main" : "success.main"} fontWeight="bold">
                                            {result.result?.is_anomaly ? "ANOMALY DETECTED" : "SYSTEM HEALTHY"}
                                        </Typography>
                                    </Box>
                                </Box>

                                <Divider sx={{ my: 2 }} />

                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Card variant="outlined">
                                            <CardContent>
                                                <Typography variant="caption" color="text.secondary">Fusion Score</Typography>
                                                <Typography variant="h3" fontFamily="monospace">
                                                    {result.result?.score_fusion?.toFixed(4) || "0.00"}
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Card variant="outlined">
                                            <CardContent>
                                                <Typography variant="caption" color="text.secondary">Confidence</Typography>
                                                <Typography variant="h3">
                                                    {((result.result?.confidence || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                </Grid>

                                <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 2, fontFamily: 'monospace', fontSize: '0.8rem', overflowX: 'auto' }}>
                                    <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                                        RAW MODEL OUTPUT:
                                    </Typography>
                                    <pre>{JSON.stringify(result, null, 2)}</pre>
                                </Box>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default MLSimulator;
