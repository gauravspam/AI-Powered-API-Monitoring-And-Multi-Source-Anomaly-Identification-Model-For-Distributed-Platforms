import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
    Container,
    Grid,
    Typography,
    Box,
    Paper,
    List,
    ListItem,
    Divider,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    IconButton,
    Tooltip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
} from "@mui/material";
import {
    Speed as SpeedIcon,
    Memory as MemoryIcon,
    Storage as StorageIcon,
    NetworkCheck as NetworkIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon,
    ErrorOutline as ErrorIcon,
    CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import api from "@/api/http";

const THROTTLE_MS = 5000;
const POLL_INTERVAL_MS = 30000;

const severityColors = {
    critical: "error",
    high: "warning",
    medium: "info",
    low: "success",
};

const serviceHealth = [
    { name: "user-service", status: "healthy", uptime: 99.99, responseTime: 45 },
    { name: "payment-service", status: "healthy", uptime: 99.95, responseTime: 120 },
    { name: "order-service", status: "healthy", uptime: 99.98, responseTime: 85 },
    { name: "product-service", status: "degraded", uptime: 98.50, responseTime: 350 },
    { name: "notification-service", status: "healthy", uptime: 99.99, responseTime: 25 },
];

export const Analytics = () => {
    const [timeRange, setTimeRange] = useState("24h");
    const [refreshing, setRefreshing] = useState(false);
    const [metrics, setMetrics] = useState({
        cpu: 45,
        memory: 62,
        network: 78,
        storage: 34,
    });
    const [anomalyTrends, setAnomalyTrends] = useState([]);
    const [anomalyCategories, setAnomalyCategories] = useState([]);
    const [topAnomalies, setTopAnomalies] = useState([]);
    const [allAnomalies, setAllAnomalies] = useState([]);

    const isMountedRef = useRef(true);
    const pollIntervalRef = useRef(null);
    const lastFetchTime = useRef(0);

    const fetchAnalyticsData = useCallback(async (isPolling = false) => {
        try {
            if (isPolling && Date.now() - lastFetchTime.current < THROTTLE_MS) {
                return;
            }

            const [kpiRes, anomaliesRes, servicesRes] = await Promise.all([
                api.get("/dashboard/kpi").catch(() => ({ data: {} })),
                api.get("/anomalies", { params: { limit: 100 } }).catch(() => ({ data: [] })),
                api.get("/services").catch(() => ({ data: [] })),
            ]);

            if (!isMountedRef.current) return;

            lastFetchTime.current = Date.now();

            const kpi = kpiRes.data || {};
            const anomalies = anomaliesRes.data || [];

            const newMetrics = {
                cpu: 35 + Math.random() * 30,
                memory: 50 + Math.random() * 25,
                network: 60 + Math.random() * 30,
                storage: 30 + Math.random() * 10,
            };
            setMetrics(newMetrics);

            const trends = [];
            for (let i = 23; i >= 0; i--) {
                trends.push({
                    hour: `${i}h`,
                    count: Math.floor(Math.random() * 10),
                });
            }
            setAnomalyTrends(trends);

            const categories = [
                { name: "Latency Spike", count: Math.floor(anomalies.length * 0.35), color: "#f44336" },
                { name: "Error Rate", count: Math.floor(anomalies.length * 0.25), color: "#ff9800" },
                { name: "Memory Leaks", count: Math.floor(anomalies.length * 0.20), color: "#2196f3" },
                { name: "CPU Surge", count: Math.floor(anomalies.length * 0.15), color: "#9c27b0" },
                { name: "Network", count: Math.floor(anomalies.length * 0.05), color: "#4caf50" },
            ];
            setAnomalyCategories(categories);

            const top = [
                { endpoint: "/api/users", count: 145, avgScore: 0.85 },
                { endpoint: "/api/payments", count: 98, avgScore: 0.72 },
                { endpoint: "/api/orders", count: 87, avgScore: 0.68 },
                { endpoint: "/api/products", count: 65, avgScore: 0.55 },
                { endpoint: "/api/notifications", count: 42, avgScore: 0.45 },
            ];
            setTopAnomalies(top);

            const mappedAnomalies = anomalies.map((a, idx) => ({
                id: a.id || idx,
                apiName: a.apiName || a.api_name || "unknown",
                endpoint: a.endpoint || a.api_name || "/api/unknown",
                method: a.method || "GET",
                severity: a.severity || "low",
                detectionTime: a.detectedAt || a.timestamp || new Date().toISOString(),
                score: a.score || a.finalAnomalyScore || 0.5,
                status: a.status || "active",
            }));
            setAllAnomalies(mappedAnomalies);

        } catch (err) {
            console.error("Error fetching analytics data:", err);
        }
    }, []);

    useEffect(() => {
        isMountedRef.current = true;

        const loadData = async () => {
            await fetchAnalyticsData(false);
        };

        loadData();

        pollIntervalRef.current = setInterval(() => {
            fetchAnalyticsData(true);
        }, POLL_INTERVAL_MS);

        return () => {
            isMountedRef.current = false;
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, [fetchAnalyticsData]);

    const handleRefresh = useCallback(() => {
        setRefreshing(true);
        lastFetchTime.current = 0;
        fetchAnalyticsData(false).finally(() => {
            if (isMountedRef.current) {
                setRefreshing(false);
            }
        });
    }, [fetchAnalyticsData]);

    const handleTimeRangeChange = useCallback((e) => {
        setTimeRange(e.target.value);
    }, []);

    const totalAnomalies = useMemo(() => {
        return topAnomalies.reduce((sum, a) => sum + a.count, 0);
    }, [topAnomalies]);

    return (
        <Container maxWidth="xl">
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold">Analytics Dashboard</Typography>
                    <Typography variant="body1" color="text.secondary">
                        Comprehensive anomaly detection analytics and trends
                    </Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Time Range</InputLabel>
                        <Select value={timeRange} label="Time Range" onChange={handleTimeRangeChange}>
                            <MenuItem value="1h">Last Hour</MenuItem>
                            <MenuItem value="24h">Last 24 Hours</MenuItem>
                            <MenuItem value="7d">Last 7 Days</MenuItem>
                            <MenuItem value="30d">Last 30 Days</MenuItem>
                        </Select>
                    </FormControl>
                    <Tooltip title="Refresh data">
                        <IconButton onClick={handleRefresh} disabled={refreshing}>
                            <RefreshIcon sx={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: "center", bgcolor: "primary.light", color: "primary.contrastText" }}>
                        <MemoryIcon sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" fontWeight="bold">{metrics.cpu.toFixed(1)}%</Typography>
                        <Typography variant="body2">CPU Usage</Typography>
                    </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: "center", bgcolor: "secondary.light", color: "secondary.contrastText" }}>
                        <MemoryIcon sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" fontWeight="bold">{metrics.memory.toFixed(1)}%</Typography>
                        <Typography variant="body2">Memory Usage</Typography>
                    </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: "center", bgcolor: "info.light", color: "info.contrastText" }}>
                        <NetworkIcon sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" fontWeight="bold">{metrics.network.toFixed(1)}%</Typography>
                        <Typography variant="body2">Network I/O</Typography>
                    </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: "center", bgcolor: "success.light", color: "success.contrastText" }}>
                        <StorageIcon sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" fontWeight="bold">{metrics.storage.toFixed(1)}%</Typography>
                        <Typography variant="body2">Storage Used</Typography>
                    </Paper>
                </Grid>
            </Grid>

            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Anomaly Detection Trends</Typography>
                        <Box sx={{ display: "flex", alignItems: "flex-end", height: 200, gap: 1, px: 2 }}>
                            {anomalyTrends.map((item, idx) => (
                                <Box key={idx} sx={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                                    <Box
                                        sx={{
                                            width: "100%",
                                            height: `${item.count * 15}px`,
                                            bgcolor: item.count > 5 ? "error.main" : item.count > 2 ? "warning.main" : "success.main",
                                            borderRadius: 1,
                                            transition: "height 0.3s",
                                        }}
                                    />
                                    <Typography variant="caption" sx={{ mt: 1, transform: "rotate(-45)", fontSize: 8 }}>
                                        {item.hour}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>
                        <Divider sx={{ my: 2 }} />
                        <Box sx={{ display: "flex", justifyContent: "space-around" }}>
                            <Box sx={{ textAlign: "center" }}>
                                <Typography variant="h5" fontWeight="bold" color="error.main">{totalAnomalies}</Typography>
                                <Typography variant="caption">Total Anomalies</Typography>
                            </Box>
                            <Box sx={{ textAlign: "center" }}>
                                <Typography variant="h5" fontWeight="bold" color="warning.main">{anomalyCategories[0]?.count || 0}</Typography>
                                <Typography variant="caption">Critical Issues</Typography>
                            </Box>
                            <Box sx={{ textAlign: "center" }}>
                                <Typography variant="h5" fontWeight="bold" color="success.main">98.5%</Typography>
                                <Typography variant="caption">Detection Rate</Typography>
                            </Box>
                        </Box>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, height: "100%" }}>
                        <Typography variant="h6" gutterBottom>Anomaly Categories</Typography>
                        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 2 }}>
                            {anomalyCategories.map((cat, idx) => (
                                <Box key={idx}>
                                    <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                                        <Typography variant="body2">{cat.name}</Typography>
                                        <Typography variant="body2" fontWeight="bold">{cat.count}</Typography>
                                    </Box>
                                    <Box sx={{ height: 8, bgcolor: "grey.200", borderRadius: 4, overflow: "hidden" }}>
                                        <Box
                                            sx={{
                                                height: "100%",
                                                width: `${(cat.count / (anomalyCategories[0]?.count || 1)) * 100}%`,
                                                bgcolor: cat.color,
                                                borderRadius: 4,
                                            }}
                                        />
                                    </Box>
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                </Grid>
            </Grid>

            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Top Anomalies by API Endpoint</Typography>
                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>API Endpoint</TableCell>
                                        <TableCell align="right">Occurrences</TableCell>
                                        <TableCell align="right">Avg Score</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {topAnomalies.map((row, idx) => (
                                        <TableRow key={idx}>
                                            <TableCell sx={{ fontFamily: "monospace" }}>{row.endpoint}</TableCell>
                                            <TableCell align="right">{row.count}</TableCell>
                                            <TableCell align="right">
                                                <Chip
                                                    size="small"
                                                    label={row.avgScore.toFixed(2)}
                                                    color={row.avgScore > 0.7 ? "error" : row.avgScore > 0.5 ? "warning" : "success"}
                                                />
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Service Health Status</Typography>
                        <List dense>
                            {serviceHealth.map((service, idx) => (
                                <Box key={idx}>
                                    <ListItem sx={{ display: "flex", justifyContent: "space-between", py: 1.5 }}>
                                        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                                            {service.status === "healthy" ? (
                                                <CheckCircleIcon color="success" />
                                            ) : (
                                                <WarningIcon color="warning" />
                                            )}
                                            <Box>
                                                <Typography variant="body1" fontWeight="bold">{service.name}</Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    Response: {service.responseTime}ms
                                                </Typography>
                                            </Box>
                                        </Box>
                                        <Box sx={{ textAlign: "right" }}>
                                            <Typography variant="body2" fontWeight="bold" color={service.status === "healthy" ? "success.main" : "warning.main"}>
                                                {service.uptime}%
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">uptime</Typography>
                                        </Box>
                                    </ListItem>
                                    <Divider />
                                </Box>
                            ))}
                        </List>
                    </Paper>
                </Grid>
            </Grid>

            <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>Detailed Anomaly Report</Typography>
                <TableContainer>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>API Name</TableCell>
                                <TableCell>Endpoint</TableCell>
                                <TableCell>Method</TableCell>
                                <TableCell>Severity</TableCell>
                                <TableCell>Detection Time</TableCell>
                                <TableCell align="right">Score</TableCell>
                                <TableCell>Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {allAnomalies.slice(0, 15).map((row, idx) => (
                                <TableRow key={row.id || idx}>
                                    <TableCell>{row.apiName}</TableCell>
                                    <TableCell sx={{ fontFamily: "monospace" }}>{row.endpoint}</TableCell>
                                    <TableCell>
                                        <Chip size="small" label={row.method} variant="outlined" />
                                    </TableCell>
                                    <TableCell>
                                        <Chip size="small" label={row.severity} color={severityColors[row.severity] || "default"} />
                                    </TableCell>
                                    <TableCell>{new Date(row.detectionTime).toLocaleString()}</TableCell>
                                    <TableCell align="right">{row.score.toFixed(2)}</TableCell>
                                    <TableCell>
                                        <Chip size="small" label={row.status} color={row.status === "active" ? "error" : "success"} variant="outlined" />
                                    </TableCell>
                                </TableRow>
                            ))}
                            {allAnomalies.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={7} align="center" sx={{ py: 4, color: "text.secondary" }}>
                                        No anomalies detected in the selected time range
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Container>
    );
};

export default Analytics;