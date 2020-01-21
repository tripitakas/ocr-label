#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado.web import UIModule


class LabelGrid(UIModule):
    def render(self, chars, status_icons, get_char_img, title_field='txt'):
        return self.render_string('label_grid.html', chars=chars, status_icons=status_icons,
                                  get_char_img=get_char_img, title_field=title_field, img_size=(64, 64))
