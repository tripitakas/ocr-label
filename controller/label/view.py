#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controller.base import BaseHandler, DbError
from utils.helper import char2indice
import controller.errors as e

img_size = (64, 64)
icons = dict(same=('ok', '已校为字与图一致'),
             doubt=('question-sign', '已校为字与图存疑、或难以辨认'),
             invalid=('exclamation-sign', '已校为无效样本，或字框切分错误'),
             changed=('edit', '校正后字与图一致'))


class LabelViewHandler(BaseHandler):
    def build_pager(self, query, total_count, page_size=20):
        cur_page = int(self.get_query_argument('page', 1))
        page_size = int(self.get_query_argument('size', 0)) or page_size
        page_no = max(1, cur_page)
        items = query.skip(page_size * (page_no - 1)).limit(page_size)
        pager = dict(cur_page=cur_page, item_count=total_count, page_size=page_size)
        return pager, list(items)

    def get_char_img(self, c):
        return self.static_url('ocr_img/chars/%s/%s%03d.jpg' % (c['page'], c['old_txt'], c['cid']))


class LabelCharsHandler(LabelViewHandler):
    URL = '/char/proof'

    def get(self):
        """ 字列表页面 """
        try:
            pager, chars = self.build_pager(self.db.char_sum.find().sort('count', -1),
                                            self.db.char_sum.count_documents({}), 100)
            self.render('label_chars.html', pager=pager, chars=chars, img_size=img_size,
                        get_char_img=self.get_char_img)
        except DbError as err:
            self.send_db_error(err)


class LabelCharHandler(LabelViewHandler):
    URL = '/char/proof/@char'

    def get(self, txt):
        """ 单字校对页面 """
        try:
            if txt not in char2indice:
                return self.send_error_response(e.no_object, message='没有此字(%s)' % txt)

            pager, chars = self.build_pager(self.db.char.find(dict(txt=txt)).sort('cc', 1),
                                            self.db.char.count_documents(dict(txt=txt)), 100)
            todo_count = self.db.char.count_documents(dict(txt=txt, result=None))
            self.render('label_char.html', txt=txt, pager=pager, chars=chars, img_size=img_size,
                        todo_count=todo_count, status_icons=icons, get_char_img=self.get_char_img)
        except DbError as err:
            self.send_db_error(err)


class ReviewCharsHandler(LabelViewHandler):
    URL = '/char/review'

    def get(self):
        """ 字审定列表页面 """
        try:
            cond = {'labeled': {'$gt': 0}}
            pager, chars = self.build_pager(self.db.char_sum.find(cond).sort('labeled', -1),
                                            self.db.char_sum.count_documents(cond), 100)
            self.render('label_chars_review.html', pager=pager, chars=chars, img_size=img_size,
                        get_char_img=self.get_char_img)
        except DbError as err:
            self.send_db_error(err)


class ReviewCharHandler(LabelViewHandler):
    URL = '/char/review/@char'

    def get(self, txt):
        """ 单字审定页面 """
        try:
            if txt != '-' and txt not in char2indice:
                return self.send_error_response(e.no_object, message='没有此字(%s)' % txt)

            r_type = self.get_query_argument('r', '')
            cond = dict(txt=txt, result={'$in': list(icons.keys())})
            if r_type:
                cond['result'] = r_type
            if txt == '-':
                cond.pop('txt')
            pager, chars = self.build_pager(self.db.char.find(cond).sort('cc', 1),
                                            self.db.char.count_documents(cond), 100)
            cond['review_by'] = None
            todo_count = self.db.char.count_documents(cond)
            self.render('label_char_review.html', txt=txt, pager=pager, chars=chars, img_size=img_size,
                        todo_count=todo_count, status_icons=icons, r_type=r_type, get_char_img=self.get_char_img)
        except DbError as err:
            self.send_db_error(err)
