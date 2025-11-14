import uuid

from django.core.management.base import BaseCommand

from apps.db.service import UserService, GroupService, TokenService, PersonalService
from common.error import UserNotFoundError
from common.utils import str2bool


class Command(BaseCommand):
    help = '管理员操作'

    user_service = UserService()
    group_service = GroupService()

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

        parser.add_argument(
            '--personal',
            type=str,
            help='创建一个地址簿',
        )

        parser.add_argument(
            '--is-admin',
            type=str,
            help='是否为管理员',
        )

    def handle(self, *args, **options):
        """处理命令逻辑。

        :param options: 命令行选项字典
        """

        if options.get('init'):
            pwd = uuid.uuid1().hex[-8:]
            if not self.user_service.get_user_by_name('admin'):
                self.user_service.create_user(
                    username='admin',
                    password=pwd,
                    email='',
                    is_superuser=True,
                    is_staff=True
                )
                print(f'管理员账号初始化成功，管理员密码：{pwd}')
            else:
                print('管理员账号已存在')

        elif options.get('user'):
            username = options.get('user')
            password = options.get('passwd')
            is_admin = str2bool(options.get('is_admin') or False)

            try:
                if password:
                    user = self.user_service.set_password(password=password, username=username)
                    TokenService().delete_token_by_user(user.username)
                    print(f'用户 {username} 已存在，已更新密码 {password}')
                if is_admin:
                    user = self.user_service.get_user_by_name(username)
                    if not user:
                        raise UserNotFoundError
                    user.is_staff = True
                    user.save()
                    print(f'用户 {username} 已存在，已更新为管理员')
            except (ValueError, UserNotFoundError):
                if self.user_service.db.objects.count() == 0:
                    is_admin = True
                    print('由于当前用户列表为空，初始化当前用户为管理员')
                self.user_service.create_user(
                    username=username,
                    password=password,
                    email='',
                    is_superuser=False,
                    is_staff=is_admin
                )
                print(f'用户 {username} 创建成功，密码 {password}')

        elif options.get('group') and options.get('user'):
            group_name = options.get('group')
            user_name = options.get('user')
            self.group_service.add_user_to_group(user_name, group_name=group_name)
        elif options.get('group'):
            group_name = options.get('group')
            self.group_service.create_group(group_name)
        elif personal := options.get('personal'):
            user = self.get_admin_user
            try:
                PersonalService().create_personal(personal_name=personal, create_user=user, personal_type='public')
            except Exception as e:
                print(f'当前已存在 Personal: {personal}')
        else:
            print('参数错误')

    @property
    def get_admin_user(self):
        return self.user_service.get_user_by_name('admin')
