#!/usr/bin/python
from wsgiref.handlers import CGIHandler
from server.py import app

CGIHandler().run(app)
