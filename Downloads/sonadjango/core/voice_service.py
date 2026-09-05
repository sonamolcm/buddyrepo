class VoiceCallService:

    def start_call(self, phone):

        print(f"Calling {phone}...")

        return {
            "status": "Success",
            "message": "Voice call initiated."
        }