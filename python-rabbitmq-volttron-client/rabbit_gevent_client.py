#!/usr/bin/env python
import pika
import ssl
import time
import json
import yaml
import os
import gevent
import rabbitmq_connector

class RabbitMQPublisher:
    """
    RabbitMQ publisher client using BlockingConnection adapter
    """
    def __init__(self):
        self.config_path = os.path.join(os.getcwd(), 'config')
        self.config_opts = None
        self.running = False
        self.connection_ready = False
        with open(self.config_path, 'r') as yaml_file:
            self.config_opts = yaml.load(yaml_file)
        self.connector = rabbitmq_connector.RabbitMQConnector(config_opts=self.config_opts)
        self.connector.connect(self.connection_callback)

    def connection_callback(self):
        print("Connection_callback")
        self.connection_ready = True
        self.running = True
        self.add_subscriptions()
        gevent.spawn(self.publish_loop)

    def add_subscriptions(self):
        """
        Subscribe to local non-volttron topic, and volttron topic expected to come from
        VOLTTRON instance over a federation link
        :return:
        """
        queue_name = "test_client_queue"
        result = self.connector.channel.queue_declare(queue=queue_name,
                                   durable=False,
                                   exclusive=True,
                                   auto_delete=False,
                                   callback=None)
        binding_key = '__pubsub__.*.devices.#'
        print("Subscribing to topic from VOLTTRON: {}".format(binding_key))
        self.connector.channel.queue_bind(exchange='volttron',
                                queue=queue_name,
                                routing_key=binding_key,
                                callback=None)
        self.connector.channel.basic_consume(self.devices_callback,
                                   queue=queue_name,
                                   no_ack=True)
        # Subscribing to topic from local RabbitMQ publisher client
        binding_key = '__pubsub__.test.hello.#'
        print("Subscribing to topic from local RabbitMQ publisher client: {}".format(binding_key))
        self.connector.channel.queue_bind(exchange='volttron',
                                          queue=queue_name,
                                          routing_key=binding_key,
                                          callback=None)
        self.connector.channel.basic_consume(self.hello_callback,
                                             queue=queue_name,
                                             no_ack=True)

    def publish_loop(self):
        """
        Publisher loop to publish message using local RabbitMQ message broker
        :return:
        """
        max_attempts = 50

        # while not self.connection_ready:
        #     gevent.sleep(0.1)
        # self.add_subscriptions()
        i=0
        headers = dict(min_compatible_version='0.1',
                       max_compatible_version='0.5')
        for i in range(0, max_attempts):
            message_body = dict(headers=headers,
                                bus='test',
                                sender='test-admin',
                                message='Hello from NON volttron client')
            routing_key = "__pubsub__.test.hello.volttron"
            print("Publishing to topic: {}, i:{}".format(routing_key, i))
            self.connector.channel.basic_publish(exchange='volttron',
                                       routing_key=routing_key,
                                       body=json.dumps(message_body)
                                       )
            gevent.sleep(1)

        if self.connection_ready:
            self.connector.disconnect()
            self.connector.close_connection()
        self.running = False

    def devices_callback(self, ch, method, properties, body):
        print("Incoming message from VOLTTRON. Topic:{}    Message: {}".format(method.routing_key, body))

    def hello_callback(self, ch, method, properties, body):
        print("Incoming message from local RabbitMQ publisher. Topic:{}    Message: {}".format(method.routing_key, body))


if __name__ == '__main__':
    # Entry point for script
    publisher = None
    try:
        publisher = RabbitMQPublisher()
        gevent.sleep(5)
        while publisher.running:
            gevent.sleep(1)
    except KeyboardInterrupt:
        if publisher.connection_ready:
            publisher.connector.disconnect()
            publisher.connector.close_connection()


