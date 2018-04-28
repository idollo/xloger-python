# -*- coding: utf-8 -*-
from . import stacker, XLogerBase
from flask import request
from .client import XLogerClient
import time
import uuid
import re
import urllib


class FlaskXLoger(XLogerBase):
    def __init__(self, app=None, config_prefix='XLOGER', disabled=False, **kwargs):
        self.client = XLogerClient
        self.provider_kwargs = kwargs
        self.config_prefix = config_prefix
        self.disabled = disabled
        stacker['xloger'] = self
        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        if self.disabled:
            return
        host = app.config.get('{0}_HOST'.format(self.config_prefix), "localhost")
        port = app.config.get('{0}_PORT'.format(self.config_prefix), "19527")
        backend = app.config.get('{0}_FILTER_BACKEND'.format(self.config_prefix), "file:///tmp/xloger.filter")
        self.client.config(host, port, filter_backend=backend)
        that = self

        @app.before_request
        def before_request():
            request.xloger_thread = that.thread()
            request.xloger_time_start = time.time()
            request.xloger_thread_data = that.thread_data()
            that.is_watched() and that.trace("threadStart", request.xloger_thread_data)

        @app.teardown_request
        def teardown_request(fn):
            tdata = getattr(request, 'xloger_thread_data', None)
            if not tdata:
                return
            tdata.update(duration=time.time()- getattr(request, "xloger_time_start", time.time()))
            that.is_watched() and that.trace("threadEnd", tdata)

    def log(self, *args):
        if not self.is_watched():
            return
        return self.traceback('log', self.traceback_point(*args))

    def thread_data(self):
        headers = request.headers
        post = ""
        content_type = getattr(request, 'content_type', None)
        if content_type and content_type.lower() == 'application/x-www-form-urlencoded':
            post = dict(request.form.items())
        else:
            post = request.data

        return dict(
            thread=getattr(request, 'xloger_thread', self.thread()),
            timestamp=time.time(),
            host=headers.get("Host", "localhost"),
            userAgent=headers.get("User-Agent", "none"),
            clientIP=self.clientip(),
            httpMethod=request.method,
            postData=post,
            requestURI=request.full_path,
            cookie=headers.get("Cookie", '')
        )

    @staticmethod
    def thread():
        headers = request.headers
        thread = uuid.uuid1().hex
        super_thread = None
        for hv, qv in (("XLoger-Thread", "xloger_thread"), ('Console-Thread', 'console_thread')):
            super_thread = headers.get(hv, request.values.get(qv, None))
            if super_thread is not None:
                break
        return '_'.join([super_thread, thread]) if super_thread else thread

    @staticmethod
    def clientip():
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
        if self.disabled:
            return False
        if hasattr(request, "xloger_watched"):
            return request.xloger_watched

        tdata = getattr(request, 'xloger_thread_data', self.thread_data())
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




