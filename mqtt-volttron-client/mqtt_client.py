import paho.mqtt.client as mqtt
import ssl
import os
import json
import gevent
import yaml

"""
MQTT client that publishes to VOLTTRON and subscribes to 'devices' topic from VOLTTRON instance.
"""
class MQTTClient:
    def __init__(self, config_path=None):
        config_path = os.path.join(os.getcwd(), 'config')
        with open(config_path, 'r') as yaml_file:
            self.config_opts = yaml.load(yaml_file)
        self.greenlet = None
        self.client = mqtt.Client()
        try:
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            # Set username and password for connecting to RabbitMQ broker
            # Please MQTT plugin for RabbitMQ broker has first enabled for this to work
            self.client.username_pw_set(self.config_opts['user'], self.config_opts['password'])

            # Set SSL certificates for authenticated connection
            self.client.tls_set(ca_certs=self.config_opts['ca_certfile'],
                           certfile=self.config_opts['client_public_cert'],
                           keyfile=self.config_opts['client_private_cert'],
                           tls_version=ssl.PROTOCOL_TLSv1)
            # Connect to RabbitMQ broker
            self.client.connect(self.config_opts['host'], self.config_opts['mqtt_port'], 60)
            self.client.loop_start()
        except KeyError as e:
            print("Missing key error {}".format(e))

        self.running = False
        self.connection_ready = False


    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Client Connected with result code {}".format(rc))
        if not rc:
            self.connection_ready = True
            self.running = True
            topic = "__pubsub__/volttron1/devices/#"
            # Subscribe to topic
            print("Subscribe to topic: {}".format(topic))
            client.subscribe(topic)

        else:
            self.connection_ready = False
            self.running = False

    def on_disconnect(self, client, userdata, rc):
        print("Client has disconnected {}".format(rc))

    def on_message(self, client, userdata, msg):
        print("Client has received message from VOLTTRON: {}".format(msg.payload))

    def publish_loop(self):
        headers = dict(min_compatible_version='0.1',
                               max_compatible_version='0.5')
        topic = "__pubsub__/volttron1/paho/hello"
        print("Inside publish loop")
        message_body = dict(headers=headers,
                            bus='mqtt',
                            sender='paho-mqtt',
                            message='Hello from MQTT client')
        while self.running:
            print("Publishing to :{}".format(topic))
            self.client.publish(topic, json.dumps(message_body))
            gevent.sleep(1)


if __name__ == '__main__':
    # Entry point for script
    mqtt_client = None
    try:
        mqtt_client = MQTTClient()
        print("Client will start publishing in 10 seconds")
        gevent.sleep(10)
        if mqtt_client.connection_ready:
            mqtt_client.publish_loop()
    except KeyboardInterrupt:
        if mqtt_client.connection_ready:
            mqtt_client.running = False
            mqtt_client.client.disconnect()
