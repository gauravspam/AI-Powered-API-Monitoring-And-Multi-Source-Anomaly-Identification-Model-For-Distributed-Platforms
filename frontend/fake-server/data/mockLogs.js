module.exports = {
    logStreams: ["service-a-stdout", "service-b-stderr"],
    logEvents: [
        { timestamp: new Date().toISOString(), level: "INFO", message: "Service started successfully" },
        { timestamp: new Date().toISOString(), level: "ERROR", message: "Connection timeout to DB" }
    ]
};
