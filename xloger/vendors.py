# -*- coding: utf-8 -*-
from . import stacker, XLogerBase
from flask import request
from .client import XLogerClient
import time
import uuid
import re


class FlaskXLoger(XLogerBase):
    def __init__(self, app=None, config_prefix='XLOGER', **kwargs):
        self.client = XLogerClient
        self.provider_kwargs = kwargs
        self.config_prefix = config_prefix
        stacker['xloger'] = self
        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        host = app.config.get('{0}_HOST'.format(self.config_prefix), "localhost")
        port = app.config.get('{0}_PORT'.format(self.config_prefix), "19527")
        self.client.config(host, port)
        that = self

        @app.before_request
        def before_request():
            request.xloger_thread = that.__thread()
            request.xloger_time_start = time.time()
            request.xloger_thread_data = that.__thread_data()
            that.is_watched() and that.trace("threadStart", request.xloger_thread_data)

        @app.teardown_request
        def teardown_request(fn):
            tdata = request.xloger_thread_data
            tdata.update(duration=time.time()-request.xloger_time_start)
            that.is_watched() and that.trace("threadEnd", tdata)

    def log(self, *args):
        if not self.is_watched():
            return
        return self.trace('log', self.__traceback_point(*args))

    def warnning(self, *args):
        return self.trace('warnning', self.__traceback_point(*args))

    def error(self, *args):
        return self.trace('error', self.__traceback_point(*args))

    def __thread_data(self):
        headers = request.headers
        return dict(
            thread=request.xloger_thread,
            timestamp=time.time(),
            host=headers.get("Host", "localhost"),
            userAgent=headers.get("User-Agent", "none"),
            clientIP=self.__clientip(),
            httpMethod=request.method,
            postData=request.data,
            requestURI=request.full_path,
            cookie=headers.get("Cookie", '')
        )

    @staticmethod
    def __thread():
        headers = request.headers
        thread = uuid.uuid1().hex
        super_thread = None
        for hv, qv in (("Xloger-Thread", "xloger_thread"), ('Console-Thread', 'console_thread')):
            super_thread = headers.get(hv, request.values.get(qv, None))
            if super_thread is not None:
                continue
        return '_'.join([super_thread, thread]) if super_thread else thread

    @staticmethod
    def __clientip():
        headers = request.headers
        for h in ("Client-IP", "X-Real-IP", "Remote-Addr"):
            ip = headers.get(h, None)
            if ip:
                return ip
        xff = headers.getlist("X-Forwarded-For")
        if xff:
            return xff[0]
        return request.remote_addr

    def is_watched(self):
        if hasattr(request, "xloger_watched"):
            return request.xloger_watched

        tdata = getattr(request, 'xloger_thread_data', self.__thread_data())
        filter = self.client.filter()
        filters = filter.get("list", [])
        server_mention = filter.get("server_mention", False)

        watched = False
        for f in filters:
            single_watched = True
            fkeys = f.items()
            for k, v in fkeys:
                exp = v.replace(".", '\.').replace("*", ".*").replace("/", "\/");
                rex = re.compile(exp, re.IGNORECASE)
                k = k.lower()
                if k == "serverip":
                    if not server_mention:
                        single_watched = False
                        break

                if k == "clientip":
                    if not rex.match(tdata['clientIP']):
                        single_watched = False
                        break

                if k == "host":
                    if not rex.match(tdata['host']):
                        single_watched = False
                        break

                if k == "useragent":
                    if not rex.match(tdata['userAgent']):
                        single_watched = False
                        break

                if k == "httpmethod":
                    if not rex.match(tdata['httpMethod']):
                        single_watched = False
                        break
                if k == "requesturi":
                    if not rex.match(tdata['requestURI']):
                        single_watched = False
                        break
            if len(fkeys) == 0:
                single_watched = False

            if single_watched:
                watched = True
                break

        request.xloger_watched = watched
        return watched




