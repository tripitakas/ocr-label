#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 导入页面文件到文档库

from glob2 import glob
from os import path
from datetime import datetime
import json
import pymongo
import fire


def update_char_sum(db, char_map, reset):
    chars = db.char.aggregate([
        {'$group': {'_id': '$txt', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])
    if reset:
        r = db.char_sum.insert_many(dict(txt=r['_id'], count=r['count'], char=char_map[r['_id']]) for r in chars)
        print('%d chars added' % len(r.inserted_ids))
    else:
        updated = []
        for c in chars:
            exist = db.char_sum.find_one(dict(txt=c['_id']))
            info = dict(count=c['count'])
            if c['_id'] in char_map:
                if not exist or exist['char']['cc'] < char_map[c['_id']]['cc']:
                    info['char'] = char_map[c['_id']]
            r = db.char_sum.update_one(dict(txt=c['_id']), {'$set': info}, upsert=True)
            if r.modified_count:
                updated.append(c['_id'])
        print('%d chars updated%s' % (len(updated), ': ' + ''.join(updated) if updated else ''))


def add_pages(json_path='', db=None, db_name='ocr_label', uri='localhost', names=None, reset=False):
    def scan_char(c):
        char_map[c['txt']] = char_map.get(c['txt'], c)
        if char_map[c['txt']]['cc'] < c['cc']:
            char_map[c['txt']] = c
        return c

    if not db:
        db = pymongo.MongoClient(uri)[db_name]
    reset = reset or db.page.count_documents({}) == 0
    if reset:
        db.page.delete_many({})
        db.char.delete_many({})
        db.char_sum.delete_many({})

    fields = ['name', 'width', 'height', 'layout', 'blocks', 'columns', 'chars',
              'ocr', 'ocr_col', 'text', 'create_time']
    char_map = {}
    if isinstance(names, str):
        names = names.split(',')

    for i, json_file in enumerate(sorted(glob(path.join(json_path, '*.json')))):
        name = path.basename(json_file).split('.')[0]
        if names and name not in names:
            continue
        exist = db.page.find_one(dict(name=name))
        if not names and not reset and exist:
            continue
        page = json.load(open(json_file))
        m = {k: v for k, v in page.items() if k in fields}

        fmt = '%s:\t%d x %d blocks=%d columns=%d chars=%d #%d'
        print(fmt % (name, m['width'], m['height'], len(m['blocks']), len(m['columns']), len(m['chars']), i + 1))

        if isinstance(m.get('create_time'), str):
            m['create_time'] = datetime.strptime(m['create_time'], '%Y-%m-%d %H:%M:%S')
        else:
            m['create_time'] = datetime.now()
        if exist:
            m.pop('create_time', None)
            db.page.update_one(dict(name=name), {'$set': m})
        else:
            db.page.insert_one(m)

        db.char.delete_many(dict(page=name))
        db.char.insert_many(scan_char(dict(page=name, txt=c['txt'], old_txt=c['txt'], cid=c['cid'], cc=c['cc'],
                                           old_id=c['char_id'], x=c['x'], y=c['y'], w=c['w'], h=c['h']))
                            for c in m['chars'])

    update_char_sum(db, char_map, reset)


if __name__ == '__main__':
    fire.Fire(add_pages)
