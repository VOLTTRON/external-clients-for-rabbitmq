#!/usr/bin/env python
import pika
import ssl
import yaml
import os

class RabbitMQSubscriber:
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
        queue_name = "test_client_queue"
        result = self.channel.queue_declare(queue_name, exclusive=True)
        binding_key = '__pubsub__.*.devices.#'
        print("Subscribing to topic: {}".format(binding_key))
        self.channel.queue_bind(exchange='volttron',
                           queue=queue_name,
                           routing_key=binding_key)
        self.channel.basic_consume(self.devices_callback,
                              queue=queue_name,
                              no_ack=True)
        binding_key = '__pubsub__.test.hello.#'
        print("Subscribing to topic: {}".format(binding_key))
        self.channel.queue_bind(exchange='volttron',
                           queue=queue_name,
                           routing_key=binding_key)
        self.channel.basic_consume(self.hello_callback,
                              queue=queue_name,
                              no_ack=True)

    def devices_callback(self, ch, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))

    def hello_callback(self, ch, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))


if __name__ == '__main__':
    # Entry point for script
    subscriber = None
    try:
        subscriber = RabbitMQSubscriber()
        subscriber.channel.start_consuming()
    except KeyboardInterrupt:
        if subscriber:
            subscriber.connection.close()

