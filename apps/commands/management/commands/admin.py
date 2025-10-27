import uuid

from django.core.management.base import BaseCommand

from apps.db.service import UserService, GroupService


class Command(BaseCommand):
    help = '管理员操作'

    def add_arguments(self, parser):
        """添加命令行参数。

        :param parser: 参数解析器对象
        """
        parser.add_argument(
            '--init',
            action='store_true',
            help='初始化管理员账号',
        )

        parser.add_argument(
            '--user',
            type=str,
            help='指定用户名',
        )

        parser.add_argument(
            '--passwd',
            type=str,
            help='指定用户密码',
        )

        parser.add_argument(
            '--group',
            type=str,
            help='指定用户组',
        )

    def handle(self, *args, **options):
        """处理命令逻辑。

        :param options: 命令行选项字典
        """
        user_service = UserService()
        group_service = GroupService()
        default_group = group_service.default_group()

        if options.get('init'):
            pwd = uuid.uuid1().hex[-8:]
            if not user_service.get_user_by_name('admin'):
                user = user_service.create_user(
                    username='admin',
                    password=pwd,
                    email='',
                    is_superuser=True,
                    is_staff=True
                )
                group_service.add_user_to_group(user, group_name=default_group)
                print(f'管理员账号初始化成功，管理员密码：{pwd}')
            else:
                print('管理员账号已存在')

        elif options.get('user') and options.get('passwd'):
            username = options.get('user')
            password = options.get('passwd')

            if user := user_service.get_user_by_name(username):
                user.set_password(password)
                print(f'用户 {username} 已存在，已更新密码 {password}')
            else:
                user_service.create_user(
                    username=username,
                    password=password,
                    email='',
                    is_superuser=False,
                    is_staff=True
                )
                print(f'用户 {username} 创建成功，密码 {password}')
        elif options.get('group') and options.get('user'):
            group_name = options.get('group')
            user_name = options.get('user')
            group_service.add_user_to_group(user_name, group_name=group_name)
        elif options.get('group'):
            group_name = options.get('group')
            group_service.create_group(group_name)
        else:
            print('参数错误')
