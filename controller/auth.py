#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 角色和权限
@time: 2019/3/13
"""

import re

# url占位符
url_placeholder = {
    'num': '[0-9]+',
    'doc_id': '[a-z0-9]{24}',
    'char': '[^/?]+',
}

""" 角色权限对应表，定义系统中的所有角色以及对应的route权限。角色可以嵌套定义。
    将属于同一业务的route分配给同一个角色，用户通过拥有角色来拥有对应的route权限。
    字段说明：
    routes：角色可以访问的权限集合；
    roles：角色所继承的父角色；
    is_assignable：角色是否可被分配。
"""
role_route_maps = {
    '单元测试用户': {
        'is_assignable': False,
        'routes': {
        }
    },
    '访客': {
        'is_assignable': False,
        'remark': '任何人都可访问，无需登录',
        'routes': {
            '/': ['GET'],
            '/home': ['GET'],
            '/api/user/login': ['GET'],
        }
    },
    '普通用户': {
        'is_assignable': False,
        'remark': '登录用户均可访问，无需授权',
        'routes': {
            '/char': ['GET'],
            '/char/@char': ['GET'],
        }
    },
    'OCR校对员': {
        'is_assignable': True,
        'roles': ['普通用户'],
        'routes': {
            '/api/label/char/@doc_id': ['GET', 'POST'],
        }
    },
    'OCR审定员': {
        'is_assignable': True,
        'roles': ['OCR校对员'],
        'routes': {
        }
    },
    '系统管理员': {
        'is_assignable': True,
        'roles': ['OCR校对员'],
        'routes': {
            '/api': ['GET'],
        }
    },
}


def get_assignable_roles():
    """可分配给用户的角色"""
    return [role for role, v in role_route_maps.items() if v.get('is_assignable')]


def can_access(role, path, method):
    """
    检查角色是否可以访问某个请求
    :param role: 可以是一个或多个角色，多个角色为逗号分隔的字符串
    :param path: 浏览器请求path
    :param method: http请求方法，如GET/POST
    """

    def match_exclude(p, exclude):
        for holder, regex in url_placeholder.items():
            if holder not in exclude:
                p = p.replace('@' + holder, '(%s)' % regex)
        route_accessible = get_role_routes(role)
        for _path, _method in route_accessible.items():
            for holder, regex in url_placeholder.items():
                if holder not in exclude:
                    _path = _path.replace('@' + holder, '(%s)' % regex)
            if (p == _path or re.match('^%s$' % _path, p) or re.match('^%s$' % p, _path)) and method in _method:
                return True
            parts = re.search(r'\(([a-z|]+)\)', _path)
            if parts:
                whole, parts = parts.group(0), parts.group(1).split('|')
                for ps in parts:
                    ps = _path.replace(whole, ps)
                    if (p == ps or re.match('^%s$' % ps, p) or re.match('^%s$' % p, ps)) and method in _method:
                        return True

    if re.search('./$', path):
        path = path[:-1]
    if match_exclude(path, []):
        return True
    if match_exclude(path, ['page_name', 'num']):
        return True
    return False


def get_role_routes(roles, routes=None):
    """ 获取指定角色对应的route集合
    :param roles: 可以是一个或多个角色，多个角色为逗号分隔的字符串
    """
    assert type(roles) in [str, list]
    if type(roles) == str:
        roles = [r.strip() for r in roles.split(',')]
    routes = dict() if routes is None else routes
    for r in roles:
        for url, m in role_route_maps.get(r, {}).get('routes', {}).items():
            routes[url] = list(set(routes.get(url, []) + m))
        # 进一步查找嵌套角色
        for r0 in role_route_maps.get(r, {}).get('roles', []):
            get_role_routes(r0, routes)
    return routes


def get_route_roles(uri, method):
    """获取能访问route(uri, method)的所有角色"""
    roles = []
    for role in role_route_maps:
        if can_access(role, uri, method) and role not in roles:
            roles.append(role)
    return roles


def get_all_roles(user_roles):
    """获取所有角色（包括嵌套角色）"""
    if isinstance(user_roles, str):
        user_roles = [u.strip() for u in user_roles.split(',')]
    roles = list(user_roles)
    for role in user_roles:
        sub_roles = role_route_maps.get(role, {}).get('roles')
        if sub_roles:
            roles.extend(sub_roles)
            for _role in sub_roles:
                roles.extend(get_all_roles(_role))
    return list(set(roles))
