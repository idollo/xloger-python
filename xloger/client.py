# -*- coding: utf-8 -*-
from socketpool import ConnectionPool, Connector, TcpConnector
import socket
import select
import errno
import time
from time import sleep
import random
import json
import warnings
import os
import tempfile

class XLogerConnector(TcpConnector):
    def sendall(self, data, flags=0):
        return self._s.send(data, flags)

    pass


tmpdir = tempfile.gettempdir()
filter_file_name = os.path.join(tempfile.gettempdir(), "xloger_filter.tmp")

class XLogerClient(object):
    """

    """
    host = None
    port = None
    pool = None
    filter = dict()

    @classmethod
    def config(cls, host="localhost", port=19100, factory=XLogerConnector):
        cls.host = host
        cls.port = port
        cls.pool = ConnectionPool(factory=factory)

        pid = os.fork()
        if pid == 0:
            pass
        else:
           cls.fork_reciever(host, port)

    @classmethod
    def fork_reciever(cls, host, port, retry=0):
        try:
            receiver = socket.create_connection((host, port))
        except socket.error, (code, message):
            warnings.warn("Connect to XLoger Server Failed: [%s] %s" % (code, message))
            sleep(3)
            cls.fork_reciever(host, port, retry+1)
            return

        # non-blocking
        receiver.setblocking(0)
        data = dict(action="register", data=dict(duplex=True, reciever=True))
        receiver.send(json.dumps(data)+'\n')

        def reconnect():
            receiver.close()
            sleep(3)
            cls.fork_reciever(host, port)

        while True:
            try:
                line = receiver.makefile().readline()
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sleep(1)
                    continue
                if err == errno.ECONNRESET:
                    reconnect()
                    break
                continue

            if line:
                cls.handle_package_data(line)
            else:
                try:
                    receiver.send(json.dumps(data)+'\n')
                except socket.error, e:
                    if e.errno == errno.ECONNRESET:
                        reconnect()
                        break

    @classmethod
    def send(cls, data):
        conn = cls.pool.get(host=cls.host, port=cls.port)
        conn.sendall(data)

    @classmethod
    def push(cls, action='log',  data=''):
        data = dict(action=action, data=data)
        stream = json.dumps(data)+'\n'
        cls.send(stream)

    @classmethod
    def handle_package_data(cls, data):
        try:
            data = json.loads(data)
        except Exception as e:
            warnings.warn("Invalid data recieved.")
            return
        action, data = data.get("action", None), data.get("data", None)
        if not action or not isinstance(data, dict):
            warnings.warn("Invalid data recieved.")
            return
        cls.dispatch(action, data)

    @classmethod
    def dispatch(cls, action, data):
        action = getattr(cls, "dispatch_"+action, None)
        callable(action) and action(data)



    @classmethod
    def dispatch_filter(cls, filter):
        f = open(filter_file_name, "w+")
        f.write(json.dumps(filter))
        f.close()

    @classmethod
    def filter(cls):
        f = open(filter_file_name, 'r+')
        data = f.read()
        if data:
            return json.loads(data)
        return dict()




