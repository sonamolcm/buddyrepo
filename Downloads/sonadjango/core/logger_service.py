import logging

logger = logging.getLogger("core")

class LoggerService:

    def info(self, message):
        logger.info(message)

    def error(self, message):
        logger.error(message)

    def ai_event(self, message):
        logger.info(f"AI EVENT: {message}")

    def retry(self, message):
        logger.warning(f"RETRY: {message}")

        