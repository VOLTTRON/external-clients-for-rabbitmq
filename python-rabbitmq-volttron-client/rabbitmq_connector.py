import pika
import logging
import json
import gevent
import gevent.monkey
import yaml
import ssl
import os

_log = logging.getLogger(__name__)
# reduce pika log level
logging.getLogger("pika").setLevel(logging.WARNING)
gevent.monkey.patch_all()

class RabbitMQConnector(object):
    """
    Class that maintains connection to RabbitMQ
    """
    def __init__(self, config_opts):
        self._connection = None
        self.config_opts = config_opts
        try:
            self._connection_param = pika.ConnectionParameters(host=self.config_opts['host'],
                                       port=self.config_opts['amqps_port'],
                                       virtual_host=self.config_opts['virtual_host'],
                                       ssl=True, ssl_options=dict(
                                        ssl_version=ssl.PROTOCOL_TLSv1,
                                        ca_certs=self.config_opts['ca_certfile'],
                                        keyfile=self.config_opts['client_private_cert'],
                                        certfile=self.config_opts['client_public_cert'],
                                        cert_reqs=ssl.CERT_REQUIRED),
                                       credentials=pika.credentials.ExternalCredentials())
        except KeyError as e:
            print("Missing key in config. Add key entry in the config and rerun the program: {}".format(e))

        self.channel = None
        self._connection_callback = None
        self._error_callback = None

    def open_connection(self):
        self._connection = pika.GeventConnection(self._connection_param,
                                                 on_open_callback=self.on_connection_open,
                                                 on_open_error_callback=self.on_open_error,
                                                 on_close_callback=self.on_connection_closed
                                                 )

    def connect(self, connection_callback=None, error_callback=None):
        self._connection_callback = connection_callback
        self._error_callback = error_callback
        self.open_connection()

    def on_connection_open(self, unused_connection):
        if self._connection is None:
            self._connection = unused_connection
        # Open a channel
        self._connection.channel(self.on_channel_open)

    def on_open_error(self, _connection_unused, error_message=None):
        # Do something
        print("Cannot open connection RabbitMQ broker")

    def on_connection_closed(self, connection, reply_code, reply_text):
        print("Connection to RabbitMQ broker closed unexpectedly")

    def on_channel_open(self, channel):
        self.channel = channel
        self.channel.exchange_declare(exchange='volttron', exchange_type='topic')

        if self._connection_callback:
            self._connection_callback()

    def disconnect(self):
        try:
            if self.channel and self.channel.is_open:
                self.channel.basic_cancel(self.on_cancel_ok)
        except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed) as exc:
            print("Connection to RabbitMQ broker or Channel is already closed.")
            self._connection.ioloop.stop()

    def on_cancel_ok(self):
        self.channel.close()
        self._connection.close()

    def close_connection(self):
        if self.channel and self.channel.is_open:
            self.channel.close()
            self._connection.close()
