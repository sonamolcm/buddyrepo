class ScheduleEmail:

    def send_confirmation(self, email):

        print(f"Interview confirmation email sent to {email}")

        return {
            "status": "Success",
            "recipient": email
        }

    