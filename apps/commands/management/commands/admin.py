import uuid

from django.core.management.base import BaseCommand

from apps.db.service import UserService


class Command(BaseCommand):
    help = '管理员操作'

    def add_arguments(self, parser):
        """添加命令行参数。

        :param parser: 参数解析器对象
        """
        parser.add_argument(
            '--set-pwd',
            type=str,
            help='指定新的admin密码',
        )

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

    def handle(self, *args, **options):
        """处理命令逻辑。

        :param options: 命令行选项字典
        """
        user_service = UserService()

        if options.get('init'):
            pwd = uuid.uuid1().hex[-8:]
            if not user_service.get_user_by_name('admin'):
                user_service.create_user(
                    username='admin',
                    password=pwd,
                    email='',
                    is_superuser=True,
                    is_staff=True
                )
                print(f'管理员账号初始化成功，管理员密码：{pwd}')
            else:
                print('管理员账号已存在')

        elif new_pwd := options.get('set_pwd'):
            if user := user_service.get_user_by_name('admin'):
                user.set_password(new_pwd)
                user.save()
                print('管理员密码修改成功')
            else:
                print('管理员账号不存在')
                user_service.create_user(
                    username='admin',
                    password=new_pwd,
                    email='',
                    is_superuser=True,
                    is_staff=True
                )
                print(f'管理员账号初始化成功，管理员密码：{new_pwd}')

        elif options.get('user') and options.get('passwd'):
            username = options.get('user')
            password = options.get('passwd')

            if user_service.get_user_by_name(username):
                print(f'用户 {username} 已存在')
            else:
                user_service.create_user(
                    username=username,
                    password=password,
                    email='',
                    is_superuser=False,
                    is_staff=True
                )
                print(f'用户 {username} 创建成功')
        else:
            print('参数错误')
