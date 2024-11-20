import os


class ConfigManager:
    @staticmethod
    def get_config(key, default=None):
        return os.getenv(key, default)
