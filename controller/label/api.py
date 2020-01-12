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
            img_url = self.get_img(char['page'])
            if page and img_url:
                char['img_url'] = img_url
                char.update(dict(img_url=img_url, width=page['width'], height=page['height']))
            self.send_data_response(char)
        except DbError as err:
            self.send_db_error(err)

    def post(self, doc_id):
        """保存单字校对内容"""
        try:
            data = self.get_request_data()
            v.validate(data, [(v.not_both_empty, 'doubt', 'invalid', 'txt')], self)
            for k in list(data.keys()):
                if k not in ['doubt', 'invalid', 'txt']:
                    data.pop(k)

            char = self.db.char.find_one({'_id': ObjectId(doc_id)})
            if char is None:
                return self.send_error_response(e.no_object, message='没有此单字')

            if data.get('txt'):
                if data['txt'] not in char2indice:
                    return self.send_error_response(e.no_object, message='无效的单字: ' + data['txt'])
                data['doubt'] = data['invalid'] = None

            r = self.db.char.update_one({'_id': char['_id']}, {'$set': data})
            if r.modified_count:
                self.db.char.update_one({'_id': char['_id']},
                                        {'$set': dict(verified=True, modified_by=self.current_user['name'],
                                                      updated_time=datetime.now())})
                self.add_op_log('label_char', target_id=char['_id'], message=str(data))
                char.update(data)

            self.send_data_response(char)
        except DbError as err:
            self.send_db_error(err)
