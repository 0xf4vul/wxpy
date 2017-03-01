import logging

from wxpy.chat import Chat
from wxpy.member import Member
from wxpy.utils.tools import wrap_user_name, ensure_list, handle_response, get_user_name


class Group(Chat):
    """
    群聊对象
    """

    def __init__(self, response):
        super(Group, self).__init__(response)
        from wxpy.chats import Chats
        self._members = Chats(source=self)
        for raw in self.get('MemberList', list()):
            member = Member(raw, self)
            member.robot = self.robot
            self._members.append(member)

    @property
    def members(self):
        """
        群聊的成员列表
        """
        if not self._members or not self._members[-1].nick_name:
            self.update_group()
        return self._members

    def __contains__(self, user):
        user = wrap_user_name(user)
        for member in self.members:
            if member == user:
                return member

    def __iter__(self):
        for member in self.members:
            yield member

    def __getitem__(self, x):
        if isinstance(x, (int, slice)):
            return self.members.__getitem__(x)
        else:
            return super(Group, self).__getitem__(x)

    def __len__(self):
        return len(self.members)

    def search(self, name=None, **attributes):
        """
        在群聊中搜索成员

        :param name: 成员名称关键词
        :param attributes: 属性键值对
        :return: 匹配的群聊成员
        """
        return self.members.search(name, **attributes)

    @property
    def owner(self):
        """
        返回群主对象
        """
        owner_user_name = self.get('ChatRoomOwner')
        if owner_user_name:
            for member in self:
                if member.user_name == owner_user_name:
                    return member
        elif self.members:
            return self[0]

    @property
    def is_owner(self):
        """
        判断所属 robot 是否为群管理员
        """
        return self.get('IsOwner') == 1 or self.owner == self.robot.self

    def update_group(self, members_details=False):
        """
        更新群聊的信息

        :param members_details: 是否包括群聊成员的详细信息 (地区、性别、签名等)
        """

        @handle_response()
        def do():
            return self.robot.core.update_chatroom(self.user_name, members_details)

        self.__init__(do())

    @handle_response()
    def add_members(self, users, use_invitation=False):
        """
        向群聊中加入用户

        :param users: 待加入的用户列表或单个用户
        :param use_invitation: 使用发送邀请的方式
        """

        return self.robot.core.add_member_into_chatroom(
            self.user_name,
            ensure_list(wrap_user_name(users)),
            use_invitation
        )

    @handle_response()
    def remove_members(self, members):
        """
        从群聊中移除用户

        :param members: 待移除的用户列表或单个用户
        """

        return self.robot.core.delete_member_from_chatroom(
            self.user_name,
            ensure_list(wrap_user_name(members))
        )

    def rename_group(self, name):
        """
        修改群聊名称

        :param name: 新的名称，超长部分会被截断 (最长32字节)
        """

        encodings = ('gbk', 'utf-8')

        trimmed = False

        for ecd in encodings:
            for length in range(32, 24, -1):
                try:
                    name = bytes(name.encode(ecd))[:length].decode(ecd)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                else:
                    trimmed = True
                    break
            if trimmed:
                break

        @handle_response()
        def do():
            if self.name != name:
                logging.info('renaming group: {} => {}'.format(self.name, name))
                return self.robot.core.set_chatroom_name(get_user_name(self), name)

        ret = do()
        self.update_group()
        return ret
