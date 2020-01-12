#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: UI模块
@file: modules.py
@time: 2018/12/22
"""
import re
import math
from tornado.web import UIModule


class Pager(UIModule):
    def render(self, pager):
        if not isinstance(pager, dict):
            pager = dict(cur_page=0, item_count=0)
        if isinstance(pager, dict) and 'cur_page' in pager and 'item_count' in pager:
            conf = self.handler.application.config['pager']
            pager['page_size'] = pager.get('page_size') or conf['page_size']  # 每页显示多少条记录
            pager['page_count'] = math.ceil(pager['item_count'] / pager['page_size'])  # 一共有多少页
            pager['display_count'] = conf['display_count']  # pager导航条中显示多少个页码
            pager['path'] = re.sub(r'[?&]page=\d+', '', self.request.uri)  # 当前path
            pager['link'] = '&' if '?' in pager['path'] else '?'  # 当前path
            gap, if_left, cur_page = int(pager['display_count'] / 2), int(pager['display_count']) % 2, pager['cur_page']
            start, end = cur_page - gap, cur_page + gap - 1 + if_left
            offset = 1 - start if start < 1 else pager['page_count'] - end if pager['page_count'] < end else 0
            start, end = start + offset, end + offset
            start = 1 if start < 1 else start
            end = pager['page_count'] if end > pager['page_count'] else end
            pager['display_range'] = range(start, end + 1)

        return self.render_string('_pager.html', pager=pager)
