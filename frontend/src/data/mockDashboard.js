// http://localhost:8080/api/dashboard/kpi
const kpiCards = [
  {
    id: 1,
    label: 'Total Requests',
    value: '2.4M',
    trend: 12.5,
    trendDirection: 'up',
    unit: '/hour',
    icon: SpeedIcon,
  },
  {
    id: 2,
    label: 'Error Rate',
    value: '2.3',
    trend: -8.2,
    trendDirection: 'down',
    unit: '%',
    icon: ErrorIcon,
  },
  {
    id: 3,
    label: 'Anomaly Rate',
    value: '0.8',
    trend: 15.3,
    trendDirection: 'up',
    unit: '%',
    icon: WarningIcon,
  },
  {
    id: 4,
    label: 'Avg Latency',
    value: '145',
    trend: -5.1,
    trendDirection: 'down',
    unit: 'ms',
    icon: TimerIcon,
  },
];

// http://localhost:8080/api/dashboard/env-summary
const environmentSummary = [
  {
    id: 1,
    name: 'On Prem',
    status: 'healthy',
    uptime: 99.98,
    errorRate: 0.5,
    anomalyCount: 3,
    requestPerMin: 45000,
  },
  {
    id: 2,
    name: 'AWS',
    status: 'healthy',
    uptime: 99.99,
    errorRate: 0.3,
    anomalyCount: 2,
    requestPerMin: 78000,
  },
  {
    id: 3,
    name: 'GCP',
    status: 'degraded',
    uptime: 99.85,
    errorRate: 2.1,
    anomalyCount: 8,
    requestPerMin: 52000,
  },
  {
    id: 4,
    name: 'Azure',
    status: 'healthy',
    uptime: 99.96,
    errorRate: 0.7,
    anomalyCount: 4,
    requestPerMin: 61000,
  },
  {
    id: 5,
    name: 'Multi Cloud',
    status: 'healthy',
    uptime: 99.94,
    errorRate: 1.2,
    anomalyCount: 6,
    requestPerMin: 34000,
  },
];

// http://localhost:8080/api/dashboard/anomalies
const recentAnomalies = [
  {
    id: 1,
    serviceName: 'auth-service',
    endpoint: '/api/v1/login',
    environment: 'AWS',
    severity: 'critical',
    type: 'latency_spike',
    detectedAt: '2025-01-20T10:35:22Z',
    status: 'investigating',
    score: 0.94,
  },
  {
    id: 2,
    serviceName: 'payment-gateway',
    endpoint: '/api/v2/process',
    environment: 'GCP',
    severity: 'high',
    type: 'error_burst',
    detectedAt: '2025-01-20T10:28:15Z',
    status: 'open',
    score: 0.87,
  },
  {
    id: 3,
    serviceName: 'user-profile',
    endpoint: '/api/v1/users/:id',
    environment: 'Azure',
    severity: 'medium',
    type: 'throughput_drop',
    detectedAt: '2025-01-20T10:15:43Z',
    status: 'mitigated',
    score: 0.72,
  },
  {
    id: 4,
    serviceName: 'notification-service',
    endpoint: '/api/v1/send',
    environment: 'On Prem',
    severity: 'low',
    type: 'auth_failure',
    detectedAt: '2025-01-20T09:58:31Z',
    status: 'investigating',
    score: 0.65,
  },
  {
    id: 5,
    serviceName: 'analytics-api',
    endpoint: '/api/v3/events',
    environment: 'Multi Cloud',
    severity: 'high',
    type: 'latency_spike',
    detectedAt: '2025-01-20T09:42:18Z',
    status: 'open',
    score: 0.89,
  },
];


// http://localhost:8080/api/dashboard/traffic
const traffic=[
    {
        "timestamp": "2026-01-10T17:19:26.501Z",
        "requestsPerSec": 34400.75350540322,
        "errorRate": 2.9688649430485,
        "anomalyScore": 0.36975227193521765
    },
    {
        "timestamp": "2026-01-10T17:20:26.501Z",
        "requestsPerSec": 38800.37000550929,
        "errorRate": 2.1150505224529725,
        "anomalyScore": 0.2418449062176216
    },
    {
        "timestamp": "2026-01-10T17:21:26.501Z",
        "requestsPerSec": 37485.193461758725,
        "errorRate": 1.6289406567757003,
        "anomalyScore": 0.11055262162725066
    },
    {
        "timestamp": "2026-01-10T17:22:26.501Z",
        "requestsPerSec": 35933.94337220709,
        "errorRate": 2.25301889082802,
        "anomalyScore": 0.18564473440985452
    },
    {
        "timestamp": "2026-01-10T17:23:26.501Z",
        "requestsPerSec": 33248.20008638303,
        "errorRate": 1.6557467609251213,
        "anomalyScore": 0.2464509045459845
    },
    {
        "timestamp": "2026-01-10T17:24:26.501Z",
        "requestsPerSec": 37817.37902328883,
        "errorRate": 1.0829604965233806,
        "anomalyScore": 0.13625609259139146
    },
    {
        "timestamp": "2026-01-10T17:25:26.501Z",
        "requestsPerSec": 36317.70653733204,
        "errorRate": 1.0049414259906622,
        "anomalyScore": 0.19164381759501709
    },
    {
        "timestamp": "2026-01-10T17:26:26.501Z",
        "requestsPerSec": 34303.19767332829,
        "errorRate": 1.9526094485767516,
        "anomalyScore": 0.1286546557677038
    },
    {
        "timestamp": "2026-01-10T17:27:26.501Z",
        "requestsPerSec": 33081.63603283954,
        "errorRate": 1.1924344386503045,
        "anomalyScore": 0.13713439728813992
    },
    {
        "timestamp": "2026-01-10T17:28:26.501Z",
        "requestsPerSec": 35443.5559530168,
        "errorRate": 2.293430137863953,
        "anomalyScore": 0.3888320253485461
    },
    {
        "timestamp": "2026-01-10T17:29:26.501Z",
        "requestsPerSec": 36342.22717601059,
        "errorRate": 1.0677704038451832,
        "anomalyScore": 0.16855071140530545
    },
    {
        "timestamp": "2026-01-10T17:30:26.501Z",
        "requestsPerSec": 36038.642162127006,
        "errorRate": 2.6450173576603575,
        "anomalyScore": 0.28772798261733307
    },
    {
        "timestamp": "2026-01-10T17:31:26.501Z",
        "requestsPerSec": 36704.506173492475,
        "errorRate": 1.1458513990147179,
        "anomalyScore": 0.1613484483771244
    },
    {
        "timestamp": "2026-01-10T17:32:26.501Z",
        "requestsPerSec": 32253.230227307697,
        "errorRate": 2.6352034414808263,
        "anomalyScore": 0.2187715723501596
    },
    {
        "timestamp": "2026-01-10T17:33:26.501Z",
        "requestsPerSec": 35801.92698909961,
        "errorRate": 3.4266020171085083,
        "anomalyScore": 0.1804597432679934
    },
    {
        "timestamp": "2026-01-10T17:34:26.501Z",
        "requestsPerSec": 34523.40964700471,
        "errorRate": 2.39379856498896,
        "anomalyScore": 0.3476864478139987
    },
    {
        "timestamp": "2026-01-10T17:35:26.501Z",
        "requestsPerSec": 37060.19377833145,
        "errorRate": 1.7988605286878627,
        "anomalyScore": 0.3970677878737702
    },
    {
        "timestamp": "2026-01-10T17:36:26.501Z",
        "requestsPerSec": 34798.502189751634,
        "errorRate": 1.8855115303883974,
        "anomalyScore": 0.35046729323571724
    },
    {
        "timestamp": "2026-01-10T17:37:26.501Z",
        "requestsPerSec": 36518.272682759234,
        "errorRate": 0.7905937863859753,
        "anomalyScore": 0.12691446062506803
    },
    {
        "timestamp": "2026-01-10T17:38:26.501Z",
        "requestsPerSec": 37543.16866680677,
        "errorRate": 1.161997372384845,
        "anomalyScore": 0.14889656056130962
    },
    {
        "timestamp": "2026-01-10T17:39:26.501Z",
        "requestsPerSec": 36820.59251407621,
        "errorRate": 2.8729772084411085,
        "anomalyScore": 0.2954474833520262
    },
    {
        "timestamp": "2026-01-10T17:40:26.501Z",
        "requestsPerSec": 35452.70152244808,
        "errorRate": 3.447889365971384,
        "anomalyScore": 0.17944619235955744
    },
    {
        "timestamp": "2026-01-10T17:41:26.501Z",
        "requestsPerSec": 36855.426327171845,
        "errorRate": 2.401769649467541,
        "anomalyScore": 0.39162342191191335
    },
    {
        "timestamp": "2026-01-10T17:42:26.501Z",
        "requestsPerSec": 37205.49157727452,
        "errorRate": 2.7889978800054775,
        "anomalyScore": 0.14837085571108471
    },
    {
        "timestamp": "2026-01-10T17:43:26.501Z",
        "requestsPerSec": 36367.43867011544,
        "errorRate": 3.36003995217093,
        "anomalyScore": 0.2718724819780431
    },
    {
        "timestamp": "2026-01-10T17:44:26.501Z",
        "requestsPerSec": 34073.65031693114,
        "errorRate": 0.5394801825913549,
        "anomalyScore": 0.36581284664304126
    },
    {
        "timestamp": "2026-01-10T17:45:26.501Z",
        "requestsPerSec": 36563.376693919505,
        "errorRate": 1.828170857573084,
        "anomalyScore": 0.19208421528538233
    },
    {
        "timestamp": "2026-01-10T17:46:26.501Z",
        "requestsPerSec": 38537.76291757025,
        "errorRate": 0.5383686431019816,
        "anomalyScore": 0.27736415917784996
    },
    {
        "timestamp": "2026-01-10T17:47:26.501Z",
        "requestsPerSec": 38497.87756971726,
        "errorRate": 0.5695801433595418,
        "anomalyScore": 0.25407446248962456
    },
    {
        "timestamp": "2026-01-10T17:48:26.501Z",
        "requestsPerSec": 35432.74198729987,
        "errorRate": 2.0513274793139935,
        "anomalyScore": 0.28550880260886413
    },
    {
        "timestamp": "2026-01-10T17:49:26.501Z",
        "requestsPerSec": 37274.3600241796,
        "errorRate": 2.5056537702596167,
        "anomalyScore": 0.1965059037799472
    },
    {
        "timestamp": "2026-01-10T17:50:26.501Z",
        "requestsPerSec": 37288.747987641946,
        "errorRate": 1.27425941852197,
        "anomalyScore": 0.17465711280759988
    },
    {
        "timestamp": "2026-01-10T17:51:26.501Z",
        "requestsPerSec": 39338.96445046771,
        "errorRate": 1.666591750262882,
        "anomalyScore": 0.17489213815772864
    },
    {
        "timestamp": "2026-01-10T17:52:26.501Z",
        "requestsPerSec": 40446.13964070149,
        "errorRate": 1.9988515077488216,
        "anomalyScore": 0.3215683851059084
    },
    {
        "timestamp": "2026-01-10T17:53:26.501Z",
        "requestsPerSec": 39763.50411546439,
        "errorRate": 2.305766289683314,
        "anomalyScore": 0.39067362937755346
    },
    {
        "timestamp": "2026-01-10T17:54:26.501Z",
        "requestsPerSec": 36907.41643231187,
        "errorRate": 2.1457227863974975,
        "anomalyScore": 0.15438381393089365
    },
    {
        "timestamp": "2026-01-10T17:55:26.501Z",
        "requestsPerSec": 38036.38954165345,
        "errorRate": 3.095648677101587,
        "anomalyScore": 0.20082522828124177
    },
    {
        "timestamp": "2026-01-10T17:56:26.501Z",
        "requestsPerSec": 39997.11563653016,
        "errorRate": 0.5905434594824601,
        "anomalyScore": 0.2623843670572684
    },
    {
        "timestamp": "2026-01-10T17:57:26.501Z",
        "requestsPerSec": 40868.48921145877,
        "errorRate": 2.1759388602973,
        "anomalyScore": 0.16413533826611762
    },
    {
        "timestamp": "2026-01-10T17:58:26.501Z",
        "requestsPerSec": 39508.62809994662,
        "errorRate": 1.933756297430895,
        "anomalyScore": 0.18658411456178076
    },
    {
        "timestamp": "2026-01-10T17:59:26.501Z",
        "requestsPerSec": 40796.89228047705,
        "errorRate": 0.8411575990908806,
        "anomalyScore": 0.3656878370617507
    },
    {
        "timestamp": "2026-01-10T18:00:26.501Z",
        "requestsPerSec": 40198.90026306224,
        "errorRate": 3.3026357143688196,
        "anomalyScore": 0.34569436102639195
    },
    {
        "timestamp": "2026-01-10T18:01:26.501Z",
        "requestsPerSec": 41081.542892634585,
        "errorRate": 1.6523832336492639,
        "anomalyScore": 0.24245439904416716
    },
    {
        "timestamp": "2026-01-10T18:02:26.501Z",
        "requestsPerSec": 42245.99443135741,
        "errorRate": 0.6818207531244602,
        "anomalyScore": 0.2812479607227558
    },
    {
        "timestamp": "2026-01-10T18:03:26.501Z",
        "requestsPerSec": 39276.72080912451,
        "errorRate": 0.8899241610545634,
        "anomalyScore": 0.19351447298979152
    },
    {
        "timestamp": "2026-01-10T18:04:26.501Z",
        "requestsPerSec": 42016.484959812165,
        "errorRate": 3.0006700744600616,
        "anomalyScore": 0.3328043651429762
    },
    {
        "timestamp": "2026-01-10T18:05:26.501Z",
        "requestsPerSec": 41959.34918996538,
        "errorRate": 2.883779914910333,
        "anomalyScore": 0.2567764225915129
    },
    {
        "timestamp": "2026-01-10T18:06:26.501Z",
        "requestsPerSec": 38442.67455625158,
        "errorRate": 1.9438556023361562,
        "anomalyScore": 0.26172185877523424
    },
    {
        "timestamp": "2026-01-10T18:07:26.501Z",
        "requestsPerSec": 39447.11725790168,
        "errorRate": 3.4966165291611055,
        "anomalyScore": 0.32894600896097004
    },
    {
        "timestamp": "2026-01-10T18:08:26.501Z",
        "requestsPerSec": 38504.62208018431,
        "errorRate": 0.6546164373676187,
        "anomalyScore": 0.1288974134775123
    },
    {
        "timestamp": "2026-01-10T18:09:26.501Z",
        "requestsPerSec": 37786.41295442369,
        "errorRate": 2.1878642521889375,
        "anomalyScore": 0.351608525369981
    },
    {
        "timestamp": "2026-01-10T18:10:26.501Z",
        "requestsPerSec": 42332.98072888245,
        "errorRate": 2.9029291485574227,
        "anomalyScore": 0.7304895531539609
    },
    {
        "timestamp": "2026-01-10T18:11:26.501Z",
        "requestsPerSec": 37783.06827269857,
        "errorRate": 1.7326084908130028,
        "anomalyScore": 0.6599394134762457
    },
    {
        "timestamp": "2026-01-10T18:12:26.501Z",
        "requestsPerSec": 39083.65306171307,
        "errorRate": 3.122641984570386,
        "anomalyScore": 0.6491221044221545
    },
    {
        "timestamp": "2026-01-10T18:13:26.501Z",
        "requestsPerSec": 36999.92742018511,
        "errorRate": 2.013033981470585,
        "anomalyScore": 0.6889006652071379
    },
    {
        "timestamp": "2026-01-10T18:14:26.501Z",
        "requestsPerSec": 41064.27661581261,
        "errorRate": 3.165876961064646,
        "anomalyScore": 0.6140055304842714
    },
    {
        "timestamp": "2026-01-10T18:15:26.501Z",
        "requestsPerSec": 36914.25502692595,
        "errorRate": 3.2222282069849144,
        "anomalyScore": 0.6573428390444979
    },
    {
        "timestamp": "2026-01-10T18:16:26.501Z",
        "requestsPerSec": 38011.56061998402,
        "errorRate": 2.6633084630288124,
        "anomalyScore": 0.8620069401162127
    },
    {
        "timestamp": "2026-01-10T18:17:26.501Z",
        "requestsPerSec": 39445.00799238518,
        "errorRate": 1.7076604928138617,
        "anomalyScore": 0.8025406142882318
    },
    {
        "timestamp": "2026-01-10T18:18:26.501Z",
        "requestsPerSec": 38351.50024994049,
        "errorRate": 3.246732183233762,
        "anomalyScore": 0.7779862004060119
    },
    {
        "timestamp": "2026-01-10T18:19:26.501Z",
        "requestsPerSec": 39921,
        "errorRate": 2.0759840901910955,
        "anomalyScore": 0.6246832755272483
    }
]




// Generate time series data for the last hour
const generateTrafficSeries = () => {
  const data = [];
  const now = new Date();
  
  for (let i = 60; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60000).toISOString();
    data.push({
      timestamp,
      requestsPerSec: Math.floor(Math.random() * 5000) + 35000 + Math.sin(i / 10) * 3000,
      errorRate: Math.random() * 3 + 0.5,
      anomalyScore: Math.random() * 0.3 + (i < 10 ? 0.6 : 0.1),
    });
  }
  
  return data;
};

export const trafficSeries = generateTrafficSeries();
