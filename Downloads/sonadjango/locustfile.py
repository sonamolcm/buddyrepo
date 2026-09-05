from locust import HttpUser, task, between


class BackendLoadTest(HttpUser):

    wait_time = between(1, 2)

    @task
    def job_list(self):
        self.client.get(
            "/api/jobs/",
            name="job-list"
        )

        