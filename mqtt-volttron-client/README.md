# Python based MQTT client for RabbitMQ based VOLTTRON

This example demonstrates the setup of having a MQTT application send and receive messages to a VOLTTRON
instance.

1. Create a VOLTTRON instance using https://volttron.readthedocs.io/en/develop/setup/index.html setup for RabbitMQ.

2. Make sure volttron is running before continuing.

3. Using the activated environment from step 1 (Note: change the paths to files below to be specific to your environment)

    a. Create a VOLTTRON private key / cert for the MQTT client to connect with
    ```
    vctl certs create-ssl-keypair paho-test
    ```

    New public cert and private key for MQTT client will be created inside $VOLTTRON_HOME. Actual path will be
    $VOLTTRON_HOME/certificates/certs/volttron1.paho-test.crt and $VOLTTRON_HOME/certificates/private/volttron1.paho-test.pem.
    Paths for these certificates will be needed later in step 7.

2. Stop VOLTTRON and RabbitMQ broker to enable MQTT plugin.

    ```
    cd <path-to-VOLTTRON-source-code>
    ./stop-volttron
    ./stop-rabbimq
    ```

3. Enable MQTT plugin

    ```
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmq-plugins enable rabbitmq_mqtt
    ```

4. Edit rabbitmq.conf in RabbitMQ installation path to add MQTT specific configuration. Path of rabbitmq.conf will be
~/rabbitmq_server/rabbitmq_server-3.7.7/etc/rabbitmq/rabbitmq.conf

   ```
   ### MQTT specific configurations
   # mqtt.listeners.tcp.default = 1883
   ## Default MQTT with TLS port is 8883
   mqtt.listeners.ssl.default = 8883
   # anonymous connections, if allowed, will use the default
   # credentials specified here
   mqtt.allow_anonymous  = true
   # Add virtual host and exchange that mqtt plugin has to use.
   # This should be the one being used by VOLTTRON instance
   mqtt.vhost            = volttron
   mqtt.exchange         = volttron
   # 24 hours by default
   mqtt.subscription_ttl = 86400000
   mqtt.prefetch         = 10
   ```

5. Restart RabbitMQ broker.

    ```
   ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmq-server -detached
   ```

6. Add a new RabbitMQ user for the MQTT client and set permissions to use VOLTTRON's virtual host

    ```
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl add_user volttron1.paho-test default
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl set_user_tags volttron1.paho-test administrator
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl set_permissions -p volttron volttron1.paho-test ".*" ".*" ".*"
    ```

7. Install master driver, listener agent and restart VOLTTRON. Tail the volttron.log to see all the incoming messages.

    ```
    cd <path-to-VOLTTRON-source-code>
    ./stop-volttron
    vcfg --agent master_driver
    ./start-volttron
    vctl start --tag master_driver
    scripts/core/upgrade-listener
    tail -f volttron.log
    ```

8. Clone python based MQTT client from github.

    ```
    cd ~
    git clone https://github.com/VOLTTRON/external-clients-for-rabbitmq.git
    cd ~/external-clients-for-rabbitmq/mqtt-volttron-client/
    ```

9. Install all the pre-requesites

    ```
    pip install -r requirements.txt
    ```

10. Update config file in MQTT client directory (cd external-clients-for-rabbitmq/mqtt-volttron-client/) with hostname,
port, self signed CA certificate of VOLTTRON instance, path of 'paho-test' client certificates, username and password of newly created user in step 6.

11. Start MQTT client on a different terminal.

    ```
    python mqtt_client.py
    ```

12. You should start seeing messages being received from VOLTTRON on the terminal.

```
26T19:28:30.001479+00:00","min_compatible_version":"5.0","max_compatible_version":"","SynchronizedTimeStamp":"2019-08-26T19:28:30.000000+00:00"},"message":[{"Heartbeat":true,"EKG_Sin":5.66553889764798e-16,"PowerState":0,"temperature":50.0,"ValveState":0},{"Heartbeat":{"units":"On/Off","tz":"US/Pacific","type":"integer"},"ValveState":{"units":"1/0","tz":"US/Pacific","type":"integer"},"PowerState":{"units":"1/0","tz":"US/Pacific","type":"integer"},"temperature":{"units":"Fahrenheit","tz":"US/Pacific","type":"integer"},"EKG_Sin":{"units":"1/0","tz":"US/Pacific","type":"integer"}}],"sender":"platform.driver","bus":""}
```

13. You should be seeing messages from MQTT client being received by listener agent. Check for these messages in volttron.log on terminal 1.

```
2019-08-26 12:28:31,037 (listeneragent-3.2 6091) listener.agent INFO: Peer: pubsub, Sender: paho-mqtt:, Bus: mqtt, Topic: paho, Headers: {'max_compatible_version': '0.5', 'min_compatible_version': '0.1'}, Message:
'Hello from MQTT client'
```