#!/usr/bin/env python
import pika
import ssl
import time
import json
import yaml
import os


class RabbitMQPublisher:
    """
    RabbitMQ publisher client using BlockingConnection adapter
    """
    def __init__(self):
        self.config_path = os.path.join(os.getcwd(), 'config')
        self.running = False
        with open(self.config_path, 'r') as yaml_file:
            self.config_opts = yaml.load(yaml_file)
        try:
            cp = pika.ConnectionParameters(host=self.config_opts['host'],
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
            print("Missing key in the config file: {}".format(e))
            print("Please add the key and restart publisher client")
        else:
            self.connection = pika.BlockingConnection(cp)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange='volttron', exchange_type='topic')
            self.running = True

    def publish_loop(self):
        max_attempts = 100
        i = 0

        headers = dict(min_compatible_version='0.1',
                       max_compatible_version='0.5')
        while self.running or (i < max_attempts):
            message_body = dict(headers=headers,
                                bus='test',
                                sender='test-admin',
                                message='Hello from NON volttron client')
            routing_key = "__pubsub__.test.hello.volttron"
            print("Publishing to topic: {}".format(routing_key))
            self.channel.basic_publish(exchange='volttron',
                                       routing_key=routing_key,
                                       body=json.dumps(message_body)
                                       )
            time.sleep(1)
            i += 1


if __name__ == '__main__':
    # Entry point for script
    publisher = None
    try:
        publisher = RabbitMQPublisher()
        if publisher.running:
            publisher.publish_loop()
    except KeyboardInterrupt:
        publisher.running = False


