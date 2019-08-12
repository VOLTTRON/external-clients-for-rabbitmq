#!/usr/bin/env python
import pika
import ssl
import time
import json
import yaml
import os


class RabbitMQPublisher:
    def __init__(self, config_path=None):
        if config_path is None or not os.path.exists(config_path) :
            self.config_path = os.path.join(os.getcwd(), 'config')
        else:
            self.config_path = config_path
        with open(self.config_path, 'r') as yaml_file:
            self.config_opts = yaml.load(yaml_file)
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
        self.connection = pika.BlockingConnection(cp)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='volttron', exchange_type='topic')

    def publish_loop(self):
        done_publishing = True
        max_attempts = 100
        i = 0

        headers = dict(min_compatible_version='0.1',
                       max_compatible_version='0.5')
        while not done_publishing or (i < max_attempts):
            message_body = dict(headers=headers,
                                bus='test',
                                sender='test-admin',
                                message='Hello from NON volttron client')

            self.channel.basic_publish(exchange='volttron',
                                       routing_key="__pubsub__.test.hello.volttron",
                                       body=json.dumps(message_body)
                                       )
            time.sleep(1)
            i += 1


if __name__ == '__main__':
    # Entry point for script
    publisher = None
    try:
        # parser = argparse.ArgumentParser()
        # parser.add_argument("config_path")
        # args = parser.parse_args()
        # print(args.config_path)

        publisher = RabbitMQPublisher()
        publisher.publish_loop()
    except KeyboardInterrupt:
        publisher.done_publishing = False

        # try:
        #     # Step #2 - Block on the IOLoop
        #     publisher.connection.ioloop.start()
        # # Catch a Keyboard Interrupt to make sure that the connection is closed cleanly
        # except KeyboardInterrupt:
        #     # Gracefully close the connection
        #     publisher.connection.close()
        #     # Start the IOLoop again so Pika can communicate, it will stop on its own when the connection is closed
        #     publisher.connection.ioloop.start()



