import os


def get_env(key, default=None):
    return os.environ.get(key, default)


class PublicConfig:
    DB_TYPE = get_env('DATABASE', 'sqlite3')
