from django.apps import AppConfig


class DbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.db'
    verbose_name = '设备数据库'
    label = 'database'

    def ready(self):
        """
        在应用就绪时为 SQLite 连接设置推荐 PRAGMA，缓解并发写入锁。

        - ``journal_mode=WAL``: 启用写前日志（WAL），提升并发读写能力；
        - ``synchronous=NORMAL``: 在 WAL 下折中性能与可靠性；
        - ``foreign_keys=ON``: 确保外键约束启用以保持一致性。

        该配置对 macOS 与 Windows 10+ 均可用。

        :return: ``None``
        :rtype: None
        """
        from django.db.backends.signals import connection_created

        def _configure_sqlite(sender, connection, **kwargs):
            """
            在新建数据库连接时进行 SQLite 专项配置。

            :param sender: 触发信号的对象
            :param connection: Django 数据库连接对象
            :type connection: django.db.backends.base.base.BaseDatabaseWrapper
            :return: ``None``
            :rtype: None
            """
            try:
                if getattr(connection, 'vendor', '') == 'sqlite':
                    cursor = connection.cursor()
                    cursor.execute('PRAGMA journal_mode=WAL;')
                    cursor.execute('PRAGMA synchronous=NORMAL;')
                    cursor.execute('PRAGMA foreign_keys=ON;')
                    cursor.close()
            except Exception:
                # 避免启动阶段因 PRAGMA 失败影响服务可用性
                pass

        # 使用 weak=False 防止回调被 GC 回收
        connection_created.connect(_configure_sqlite, weak=False)
