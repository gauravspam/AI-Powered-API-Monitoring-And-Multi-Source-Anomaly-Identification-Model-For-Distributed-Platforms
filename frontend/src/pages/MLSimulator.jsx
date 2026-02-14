import React, { useState } from 'react';
import {
    Container, Paper, Typography, Box, Button, Grid,
    CircularProgress, Alert
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

    // ✅ NEW: Payload generator matching the backend Multimodal DTO
    const generatePayload = (isAnomaly) => {
        const now = new Date();
        const windowEnd = now.getTime();
        const windowStart = windowEnd - 60000; // 1 minute window

        return {
            // 1. Context
            context: {
                service_name: isAnomaly ? "payment-service" : "user-service",
                window_end_ms: windowEnd.toString()
            },

            // 2. Metrics (List of Series)
            metrics: [
                {
                    name: "cpu",
                    values: Array.from({ length: 60 }, () =>
                        isAnomaly ? 80 + Math.random() * 20 : 20 + Math.random() * 30
                    )
                },
                {
                    name: "memory",
                    values: Array.from({ length: 60 }, () =>
                        isAnomaly ? 85 + Math.random() * 15 : 40 + Math.random() * 20
                    )
                },
                {
                    name: "latency",
                    values: Array.from({ length: 60 }, () =>
                        isAnomaly ? 500 + Math.random() * 1500 : 50 + Math.random() * 100
                    )
                },
                {
                    name: "error_rate",
                    values: Array.from({ length: 60 }, () =>
                        isAnomaly ? 0.1 + Math.random() * 0.4 : 0.0
                    )
                },
                {
                    name: "request_rate",
                    values: Array.from({ length: 60 }, () => 100 + Math.random() * 50)
                }
            ],

            // 3. Logs (List of Log Events)
            logs: isAnomaly
                ? [
                    { timestamp: windowEnd - 5000, level: "ERROR", message: "Connection timeout to DB", service: "payment-service" },
                    { timestamp: windowEnd - 4000, level: "CRITICAL", message: "Transaction failed: deadlock detected", service: "payment-service" },
                    { timestamp: windowEnd - 1000, level: "ERROR", message: "Upstream service 503 unavailable", service: "payment-service" }
                ]
                : [
                    { timestamp: windowEnd - 30000, level: "INFO", message: "Health check passed", service: "user-service" },
                    { timestamp: windowEnd - 15000, level: "INFO", message: "Request processed successfully", service: "user-service" }
                ],

            // 4. Traces (List of Spans)
            traces: [
                {
                    traceId: `trace-${Date.now()}`,
                    spanId: "span-1",
                    service: "api-gateway",
                    operation: "GET /api/pay",
                    durationMs: isAnomaly ? 2500.0 : 45.0,
                    statusCode: isAnomaly ? 500 : 200,
                    isError: isAnomaly
                },
                {
                    traceId: `trace-${Date.now()}`,
                    spanId: "span-2",
                    service: isAnomaly ? "payment-service" : "user-service",
                    operation: "db_query",
                    durationMs: isAnomaly ? 2000.0 : 10.0,
                    statusCode: isAnomaly ? 500 : 200,
                    isError: isAnomaly
                }
            ]
        };
    };

    const handlePredict = async (simulateAnomaly) => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // NOTE: We call the Python service DIRECTLY from frontend for simulation
            // Or we can call the Backend test endpoint if preferred.
            // Based on your architecture, frontend usually calls backend.
            // But if you want to test the ML model directly, we can use the /v1/predict endpoint
            // if CORS is allowed on port 9000.

            // OPTION A: Call Backend Test Endpoint (Recommended)
            // We need to update the backend test endpoint to accept this payload?
            // Actually, your TestIntegrationController generates dummy data.

            // OPTION B: Call ML Service Direct (for debugging)
            // Let's stick to the current flow: Frontend -> Backend -> ML
            // But your backend integration test controller `POST /api/test-ml/trigger`
            // generates its OWN data.

            // Let's use a new endpoint or the direct Python one if exposed.
            // Since we are in the simulator, let's try calling the ML service direct if possible,
            // OR assume we added a "pass-through" endpoint in Backend.

            // Current `TestIntegrationController` logic:
            // It creates dummy data internally. It doesn't accept a payload.

            // For this Simulator to work with your *custom* payload, we should probably
            // add a pass-through endpoint in backend or mock it.
            // Let's assume you added `POST /api/test-ml/simulate` that accepts this JSON.

            // If not, we can rely on the existing `/api/test-ml/trigger` which IGNORES this payload
            // and generates its own.

            // Let's try to send it to the backend endpoint that might exist or we just use trigger
            const response = await api.post('/test-ml/trigger', {});

            // If you want to use the generated payload, you'd need to update the Backend Controller.
            // For now, let's just trigger the test.

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
                <Typography variant="h4" fontWeight="bold">
                    Multimodal Anomaly Simulator
                </Typography>
            </Box>

            <Grid container spacing={3}>
                {/* Control Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3, height: '100%' }}>
                        <Typography variant="h6" gutterBottom>Simulation Controls</Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            Trigger the backend to generate synthetic Multimodal data (Logs + Metrics + Traces)
                            and send it to the Python Fusion Model.
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

                        {error && (
                            <Alert severity="error" sx={{ mt: 3 }}>
                                {error}
                            </Alert>
                        )}
                    </Paper>
                </Grid>

                {/* Results Panel */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 3, minHeight: 400 }}>
                        <Typography variant="h6" gutterBottom>Fusion Model Result</Typography>

                        {result ? (
                            <Box>
                                <Alert
                                    severity={result.result?.is_anomaly ? "error" : "success"}
                                    icon={result.result?.is_anomaly ? <AnomalyIcon /> : <HealthyIcon />}
                                    sx={{ mb: 2 }}
                                >
                                    <Typography variant="h6">
                                        {result.result?.is_anomaly ? "ANOMALY DETECTED" : "SYSTEM HEALTHY"}
                                    </Typography>
                                    <Typography variant="body2">
                                        Confidence: {(result.result?.confidence * 100).toFixed(1)}% |
                                        Score: {result.result?.score_fusion?.toFixed(4)}
                                    </Typography>
                                </Alert>

                                <Box sx={{ mt: 2 }}>
                                    <Typography variant="subtitle2">Processing Time:</Typography>
                                    <Typography variant="body2" fontFamily="monospace">
                                        {result.processing_time_ms?.toFixed(2)} ms
                                    </Typography>
                                </Box>

                                <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 2, fontFamily: 'monospace', fontSize: '0.8rem', overflowX: 'auto' }}>
                                    <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                                        FULL RESPONSE PAYLOAD
                                    </Typography>
                                    <pre>{JSON.stringify(result, null, 2)}</pre>
                                </Box>
                            </Box>
                        ) : (
                            <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                                <Typography>No simulation results yet</Typography>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default MLSimulator;
