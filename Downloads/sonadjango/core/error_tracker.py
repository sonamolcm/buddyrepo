class ErrorTracker:

    def track_error(self, error_message):

        return {
            "status": "Error Recorded",
            "error": error_message
        }

    def track_retry(self, operation):

        return {
            "status": "Retry Recorded",
            "operation": operation
        }
    