// Save as: generate_synthetic_logs.js
const fs = require('fs');

const services = ['auth-service', 'payment-gateway', 'inventory-service', 'notification-service', 'analytics-api'];
const environments = ['AWS', 'GCP', 'Azure', 'On Prem', 'Multi Cloud'];

function generateSyntheticLogs(count = 5000) {
  const logs = [];
  
  for (let i = 0; i < count; i++) {
    const isAnomaly = Math.random() < 0.2; // 20% anomalies
    
    logs.push({
      api_name: services[Math.floor(Math.random() * services.length)],
      response_time: isAnomaly ? 
        Math.random() * 15000 + 5000 :     // 5-20s (bad)
        Math.random() * 300 + 50,          // 50-350ms (good)
      status_code: isAnomaly ? 
        [400, 500, 502, 503][Math.floor(Math.random() * 4)] :
        [200, 201, 204][Math.floor(Math.random() * 3)],
      request_count: isAnomaly ? 
        Math.random() * 8000 + 2000 :      // High traffic
        Math.random() * 500 + 10,          // Normal
      error_rate: isAnomaly ? 
        Math.random() * 0.6 + 0.4 :        // 40-100%
        Math.random() * 0.05,              // 0-5%
      cpu_usage: isAnomaly ? 
        Math.random() * 0.25 + 0.75 :      // 75-100%
        Math.random() * 0.5 + 0.1,         // 10-60%
      memory_usage: isAnomaly ? 
        Math.random() * 0.25 + 0.75 :      // 75-100%
        Math.random() * 0.5 + 0.1,         // 10-60%
      network_io: isAnomaly ? 
        Math.random() * 1000 + 500 :       // High
        Math.random() * 100 + 10,          // Normal
      disk_io: isAnomaly ? 
        Math.random() * 500 + 200 :        // High
        Math.random() * 50 + 5,            // Normal
      hour_of_day: new Date().getHours(),
      day_of_week: new Date().getDay(),
      environment: environments[Math.floor(Math.random() * environments.length)],
      timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
    });
  }
  
  fs.writeFileSync('synthetic_logs.json', JSON.stringify(logs, null, 2));
  console.log(`✅ Generated ${logs.length} realistic logs!`);
}

generateSyntheticLogs(10000);
