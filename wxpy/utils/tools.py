import inspect
from functools import wraps

import re


def handle_response(to_class=None):
    """
    装饰器：检查从 itchat 返回的字典对象，并将其转化为指定类的实例
    若返回值不为0，会抛出 ResponseError 异常

    :param to_class: 需转化成的类，若为None则不转换
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            from wxpy.chats import Chats
            from wxpy.group import Group
            from wxpy.groups import Groups
            from wxpy.response import Response

            ret = func(*args, **kwargs)

            if not ret:
                return

            if args:
                self = args[0]
            else:
                self = inspect.currentframe().f_back.f_locals.get('self')
            from wxpy.bot import Robot
            if isinstance(self, Robot):
                robot = self
            else:
                robot = getattr(self, 'robot', None)
                if not robot:
                    raise ValueError('robot not found:m\nmethod: {}\nself: {}\nrobot: {}'.format(
                        func, self, robot
                    ))

            ret = list_or_single(Response, ret, robot)

            if to_class:
                ret = list_or_single(to_class, ret)

            if isinstance(ret, list):
                if to_class is Group:
                    ret = Groups(ret)
                elif to_class:
                    ret = Chats(ret)

            return ret

        return wrapped

    return decorator


def ensure_list(x, except_false=True):
    """
    若传入的对象不为列表，则转化为列表

    :param x:
    :param except_false: None, False 等例外，会直接返回原值
    :return: 列表，或 None, False 等
    """
    if x or not except_false:
        return x if isinstance(x, (list, tuple)) else [x]


def match_name(chat, keywords):
    """
    检查一个 Chat 对象是否匹配所有名称关键词 (若关键词为空则直接认为匹配)

    :param chat: Chat 对象
    :param keywords: 名称关键词，可用空格分割
    :return: 匹配则返回 True，否则 False
    """
    if keywords:
        if isinstance(keywords, str):
            keywords = re.split(r'\s+', keywords)
        keywords = list(map(lambda x: x.lower(), keywords))
        for kw in keywords:
            for attr in 'nick_name', 'alias', 'remark_name', 'display_name':
                if kw in str(getattr(chat, attr, '')).lower():
                    break
            else:
                return False
    return True


def list_or_single(func, i, *args, **kwargs):
    """
    将单个对象或列表中的每个项传入给定的函数，并返回单个结果或列表结果，类似于 map 函数

    :param func: 传入到的函数
    :param i: 列表或单个对象
    :param args: func 函数所需的 args
    :param kwargs: func 函数所需的 kwargs
    :return: 若传入的为列表，则以列表返回每个结果，反之为单个结果
    """
    if isinstance(i, list):
        return list(map(lambda x: func(x, *args, **kwargs), i))
    else:
        return func(i, *args, **kwargs)


def wrap_user_name(user_or_users):
    """
    确保将用户转化为带有 UserName 键的用户字典

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 单个用户字典，或列表形式的多个用户字典
    """
    return list_or_single(
        lambda x: x if isinstance(x, dict) else {'UserName': user_or_users},
        user_or_users
    )


def get_user_name(user_or_users):
    """
    确保将用户转化为 user_name 字串

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 返回单个 user_name 字串，或列表形式的多个 user_name 字串
    """
    return list_or_single(
        lambda x: x['UserName'] if isinstance(x, dict) else x,
        user_or_users
    )
