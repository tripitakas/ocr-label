#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controller.com import invalid
from controller import com, label

views = com.views + label.views

handlers = com.handlers + label.handlers
handlers += [invalid.ApiTable]

modules = com.modules

InvalidPageHandler = invalid.InvalidPageHandler
