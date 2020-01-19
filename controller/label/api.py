#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from bson.objectid import ObjectId
from datetime import datetime
from controller.base import BaseHandler, DbError
import controller.errors as e
import controller.validate as v
from utils.helper import char2indice


class LabelCharApi(BaseHandler):
    URL = ['/api/label/char/@doc_id', '/api/label/char/review/@doc_id']

    def get(self, doc_id):
        """获取待校对的单字内容"""
        try:
            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                return self.send_error_response(e.no_object, message='没有此单字')
            page = self.db.page.find_one({'name': char['page']})
            col_id = re.sub(r'c\d+$', '', char['old_id'])
            img = self.static_url('ocr_img/col/%s/%s.jpg' % (char['page'], col_id))
            col = [c for c in page['columns'] if c['column_id'] == col_id]
            if page and img and col:
                char['x'] -= col[0]['x']
                char['y'] -= col[0]['y']
                char.update(dict(img=img, width=col[0]['w'], height=col[0]['h']))
            self.send_data_response(char)
        except DbError as err:
            self.send_db_error(err)

    def post(self, doc_id):
        """保存单字校对内容"""
        try:
            data = self.get_request_data()
            if data.get('ids'):
                return self.batch_pass(data)

            v.validate(data, [(v.not_empty, 'result'),
                              (v.in_list, 'result', ['doubt', 'invalid', 'changed'])], self)
            assert (data['result'] != 'changed') == (not data.get('txt'))

            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                return self.send_error_response(e.no_object, message='没有此单字')
            if char.get('review_by') and 'review' not in self.request.path:
                return self.send_error_response(e.unauthorized, message='已审核，不能再校对')

            if data.get('txt'):
                if data['txt'] not in char2indice:
                    return self.send_error_response(e.no_object, message='无效的单字: ' + data['txt'])
                r = self.db.char.update_one({'_id': char['_id']},
                                            {'$set': dict(txt=data['txt'], result=data['result'])})
            else:
                r = self.db.char.update_one({'_id': char['_id']}, {'$set': dict(result=data['result'])})
            if r.modified_count:
                by = 'review' if 'review' in self.request.path else 'proof'
                by = {by + '_by': self.current_user['name'], by + '_time': datetime.now()}
                self.db.char.update_one({'_id': char['_id']}, {'$set': by})
                self.add_op_log('label_char', target_id=char['_id'],
                                message='%s %s' % (data['result'], data.get('txt', '')))
                char.update(data)
                self.update_labeled_count(char['old_txt'])

            self.send_data_response(char)
        except DbError as err:
            self.send_db_error(err)

    def get_line_img(self, c):
        return self.static_url('ocr_img/col/%s/b%dc%d.jpg' % (c['page'], c['block_no'], c['line_no']))

    def batch_pass(self, data):
        result = []
        to_update = set()
        by = 'review' if 'review' in self.request.path else 'proof'
        by = {by + '_by': self.current_user['name'], by + '_time': datetime.now()}

        for doc_id in data['ids']:
            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                result.append(None)
                continue

            if 'review' in self.request.path:
                self.db.char.update_one({'_id': char['_id']}, {'$set': by})
                to_update.add(char['old_txt'])
            elif not char.get('result'):
                r = self.db.char.update_one({'_id': char['_id']}, {'$set': dict(result='same')})
                if r.modified_count:
                    self.db.char.update_one({'_id': char['_id']}, {'$set': by})
                    char['result'] = 'same'
                    to_update.add(char['old_txt'])
            if not to_update:
                to_update.add(char['old_txt'])

            result.append(char['result'])

        for c in to_update:
            self.update_labeled_count(c)
        self.send_data_response(dict(result=result))

    def update_labeled_count(self, txt):
        if 'review' in self.request.path:
            cond = dict(old_txt=txt, review_by={'$ne': None})
            review_count = self.db.char.count_documents(cond)
            self.db.char_sum.update_one(dict(txt=txt), {'$set': dict(review_count=review_count)})
        else:
            cond = dict(old_txt=txt, result={'$ne': None})
            labeled = self.db.char.count_documents(cond)
            self.db.char_sum.update_one(dict(txt=txt), {'$set': dict(labeled=labeled)})
