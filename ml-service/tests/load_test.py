from locust import HttpUser, between, task


class MLServiceUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def predict(self):
        payload = {
            "context": {
                "service_name": "load-test",
                "window_start_ms": 1707648000000,
                "window_end_ms": 1707648060000
            },
            "metrics": [{"name": "cpu", "values": [0.5] * 10}],
            "logs": [{"timestamp": 1707648000000, "level": "INFO", "template": "test"}],
            "traces": []
        }

        self.client.post("/v1/predict", json=payload)
