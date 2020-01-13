#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import view, api

views = [
    view.LabelCharsHandler, view.LabelCharHandler, view.ReviewCharsHandler, view.ReviewCharHandler,
]
handlers = [
    api.LabelCharApi,
]
