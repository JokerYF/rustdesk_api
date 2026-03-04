import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

_SQLITE_PRAGMAS = (
    'PRAGMA journal_mode=WAL;',
    'PRAGMA busy_timeout=30000;',
    'PRAGMA synchronous=NORMAL;',
    'PRAGMA foreign_keys=ON;',
    'PRAGMA cache_size=-64000;',
    'PRAGMA wal_autocheckpoint=100;',
)


class DbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.db'
    verbose_name = '设备数据库'

    def ready(self):
        from django.db.backends.signals import connection_created

        def _configure_sqlite(sender, connection, **kwargs):
            try:
                if getattr(connection, 'vendor', '') == 'sqlite':
                    cursor = connection.cursor()
                    for pragma in _SQLITE_PRAGMAS:
                        cursor.execute(pragma)
                    cursor.close()
            except Exception as e:
                logger.warning(f"SQLite PRAGMA 设置失败: {e}")

        connection_created.connect(_configure_sqlite, weak=False)
