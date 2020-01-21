#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import view, api, modules

views = [
    view.LabelCharsHandler, view.LabelCharHandler, view.ReviewCharsHandler, view.ReviewCharHandler,
    view.EditCharBoxHandler,
]
handlers = [
    api.LabelCharApi,
]
modules = {
    'LabelGrid': modules.LabelGrid,
}
