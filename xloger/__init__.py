# -*- coding: utf-8 -*-
from functools import partial
from werkzeug.local import LocalStack, LocalProxy
from traceback import extract_tb, extract_stack
from sys import exc_info
import json
import time

stacker = {"xloger": None}


def _lookup_(name):
    return stacker[name]

xloger = LocalProxy(partial(_lookup_, "xloger"))


class XLogerBase(object):

    def clientip(self):
        raise NotImplementedError()

    def thread(self):
        raise NotImplementedError()

    def thread_data(self):
        raise NotImplementedError()

    def log(self, *args):
        return self.traceback('log', self.traceback_point(*args))

    def warning(self, *args):
        return self.traceback('warning', self.traceback_point(*args))

    def error(self, *args):
        return self.traceback('error', self.traceback_point(*args))

    def show_error(self, errtype, message, file, line):
        data = dict(
            file=file,
            line=line,
            message="%s: %s" % (errtype, message),
            args=[]
        )
        return self.traceback('error', data)

    def traceback(self, ttype, data):
        fire = json.dumps(data)
        post = dict(
            type=ttype,
            fire=fire
        )
        post.update(self.thread_data())
        return self.client.push('trace', post)

    def trace(self, action, data=dict()):
        data.update(type=action)
        return self.client.push('trace', data)

    def traceback_point(self, *args):
        tbs = extract_stack()
        tbs.reverse()
        fetch = False
        for file, line, func, t in tbs[1:]:
            if fetch:
                return dict(
                    file=file,
                    line=line,
                    message=args[0] if len(args)>0 else "no-message",
                    args=args
                )
            if func.lower() in ('log', 'warning', 'error'):
                fetch = True
                continue
        return None
