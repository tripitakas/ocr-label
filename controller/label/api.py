#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
from datetime import datetime
from controller.base import BaseHandler, DbError
import controller.errors as e
import controller.validate as v
from utils.helper import char2indice


class LabelCharApi(BaseHandler):
    URL = '/api/label/char/@doc_id'

    def get(self, doc_id):
        """获取待校对的单字内容"""
        try:
            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                return self.send_error_response(e.no_object, message='没有此单字')
            page = self.db.page.find_one({'name': char['page']})
            img = self.get_img(char['page'])
            if page and img:
                char['img'] = img
                char.update(dict(img=img, width=page['width'], height=page['height']))
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

            if data.get('txt'):
                if data['txt'] not in char2indice:
                    return self.send_error_response(e.no_object, message='无效的单字: ' + data['txt'])
                r = self.db.char.update_one({'_id': char['_id']},
                                            {'$set': dict(txt=data['txt'], result=data['result'])})
            else:
                r = self.db.char.update_one({'_id': char['_id']}, {'$set': dict(result=data['result'])})
            if r.modified_count:
                self.db.char.update_one({'_id': char['_id']},
                                        {'$set': dict(modified_by=self.current_user['name'],
                                                      updated_time=datetime.now())})
                self.add_op_log('label_char', target_id=char['_id'],
                                message='%s %s' % (data['result'], data.get('txt', '')))
                char.update(data)

            self.send_data_response(char)
        except DbError as err:
            self.send_db_error(err)

    def batch_pass(self, data):
        result = []
        for doc_id in data['ids']:
            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                result.append(None)
                continue

            if not char.get('result'):
                r = self.db.char.update_one({'_id': char['_id']}, {'$set': dict(result='same')})
                if r.modified_count:
                    self.db.char.update_one({'_id': char['_id']},
                                            {'$set': dict(modified_by=self.current_user['name'],
                                                          updated_time=datetime.now())})
                    char['result'] = 'same'
            result.append(char['result'])

        self.send_data_response(dict(result=result))
