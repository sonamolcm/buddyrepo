class ReminderAPI:

    def send_email_reminder(self, email):

        print(f"Reminder email sent to {email}")

        return {
            "status": "Success",
            "recipient": email
        }

    def send_voice_reminder(self, phone):

        print(f"Voice reminder initiated for {phone}")

        return {
            "status": "Success",
            "phone": phone
        }

    