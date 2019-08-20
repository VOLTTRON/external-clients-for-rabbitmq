# Python based RabbitMQ client for VOLTTRON

This example demonstrates the setup of having a non-VOLTTRON RabbitMQ application send and receive messages to a VOLTTRON
instance using federation and shovel connection. The non-VOLTTRON RabbitMQ application and VOLTTRON instance will be running
in 2 separate machines each connected to it's own broker.

1. On machine 1, create a VOLTTRON instance using https://volttron.readthedocs.io/en/develop/setup/index.html setup for RabbitMQ.
2. Make sure volttron is running before continuing.
3. On machine 2, clone TLS generation tool to generate SSL certificates. Please note, this tool needs python3 so please ensure python is installed before continuing.
    ```
    cd ~
    git clone https://github.com/schandrika/tls-gen.git
    cd ~/tls-gen/basic
    ```
4. Create self-signed CA signed certificate, server and client certificate pairs (public, private) signed
by same CA.
    ```
    make PASSWORD=test123
    ```
    Certifcates will be generated inside 'result' directory.

5. Generate another pair of client certificates using the below command with CN=<client name>. The CN parameter value provided will be the name of the user that would connect to machine 1 RabbitMQ server.
   ```
   make client-cert CN=test-admin
   ```
   New set of client certificates will be generated in results folder. Look for test-admin_certificate.pem and test-admin_key.pem

6. Clone non VOLTTRON RabbitMQ client example.
   ```
   cd ~
   git clone https://github.com/VOLTTRON/external-clients-for-rabbitmq.git
   ```

7. Install Erlang packages. You will need sudo access for this. 
   ```
   cd external-clients-for-rabbitmq/python-rabbitmq-volttron-client/
   ./rabbit_dependencies.sh <os> <version>
   ```
   OS can be 'debian' or 'centos'. Distribution names: 'xenial', 'bionic' etc. for debian. 6 or 7 for centos

8. Download non-sudo RabbitMQ.
    ```
    cd ~
    wget https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.7.7/rabbitmq-server-generic-unix-3.7.7.tar.xz
    mkdir rabbitmq_server
    tar -xf ~/rabbitmq-server-generic-unix-3.7.7.tar.xz --directory ./rabbitmq_server/
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmq-plugins enable rabbitmq_management rabbitmq_federation  rabbitmq_federation_management rabbitmq_shovel rabbitmq_auth_mechanism_ssl rabbitmq_shovel_management rabbitmq_amqp1_0
    ```

9. Install other python modules needed for running the test client
   ```
   cd ~/external-clients-for-rabbitmq/python-rabbitmq-volttron-client
   pip install -r requirements.txt
   ```

10. Configure RabbitMQ server to use SSL certificates generated in step 4. Modify rabbitmq.conf in the current directory (~/external-clients-for-rabbitmq/python-rabbitmq-volttron-client) such that ssl options are pointing to newly created certificates in step 4.

    ```
    ssl_options.cacertfile = "path to self signed CA certificate. <home>/<tls-gen-checkout-dir>/basic/result/ca_certificate.pem"
    ssl_options.certfile = "path to public certificate of server. <home>/<tls-gen-checkout-dir>/basic/result/server_certificate.pem"
    ssl_options.keyfile = "path to private certificate of server. <home>/<tls-gen-checkout-dir>/basic/result/server_key.pem"
    management.listener.ssl_opts.cacertfile = "path to self signed CA certificate. <home>/<tls-gen-checkout-dir>/basic/result/ca_certificate.pem"
    management.listener.ssl_opts.certfile = "path to public certificate of server. <home>/<tls-gen-checkout-dir>/basic/result/server_certificate.pem"
    management.listener.ssl_opts.keyfile = "path to private certificate of server. <home>/<tls-gen-checkout-dir>/basic/result/server_key.pem"
    ```

> [!NOTE]
> If you don't want to use default port. Modify these as well in the rabbitmq.conf file

11. Copy rabbitmq.conf to RabbitMQ installation path and restart RabbitMQ.
   ```
   cp rabbitmq.conf ~/rabbitmq_server/rabbitmq_server-3.7.7/etc/rabbitmq/
   ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl stop
   ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmq-server -detached
   ```

12. Create virtual host and test-admin user. The user name (in this case, test-admin) should match the  value passed to CN parameter in step 5 (make client-cert CN=test-admin)
    ```
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl add_vhost test
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl add_user test-admin default
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl set_user_tags test-admin administrator
    ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl -p test set_permissions test-admin ".*" ".*" ".*"
    ```

13. Update the file config in the current directory((~/external-clients-for-rabbitmq/python-rabbitmq-volttron-client/config) to have the correct hostname of the machine, the cert file paths, and rabbitmq ports (cert file paths and ports should match corresponding values set in step 10). The value of virtual_host and user should match the values provided in add_vhost and add_user commands in Step 12.

14. Start RabbitMQ client program that publishes and subscribes to same topic '__pubsub__.test.hello.#'. You should start
seeing the data being received. 
    ```
    python rabbitmq_gevent_publisher.py
    ```
On machine 2 terminal, you will be able to see data being received for topic- 'Topic:__pubsub__.test.hello.volttron':
    ```
    Connection_callback
    Subscribing to topic from VOLTTRON: __pubsub__.*.devices.#
    Subscribing to topic from local RabbitMQ publisher client: __pubsub__.test.hello.#
    Publishing to topic: __pubsub__.test.hello.volttron, i:0
    Publishing to topic: __pubsub__.test.hello.volttron, i:1
    Incoming message from VOLTTRON. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
    Publishing to topic: __pubsub__.test.hello.volttron, i:2
    Incoming message from local RabbitMQ publisher. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
    Publishing to topic: __pubsub__.test.hello.volttron, i:3
    Incoming message from VOLTTRON. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
    Publishing to topic: __pubsub__.test.hello.volttron, i:4
    Incoming message from local RabbitMQ publisher. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
    ```
This verifies that we are able to successfully subscribe andd publish to the local message bus. 

## Federation Setup:

1. Copy the self signed root CA certificates from machine 1 to machine 2 and vice versa using scp command. For example to copy from machine 1 (volttron) to machine 2(non volttron)

    ```
    scp $VOLTTRON_HOME/certificates/certs/<volttron_instancename>-root-ca.crt <user>@<machine2 ip or hostname>:<path on machine2>
    ```
And to copy from machine 2 to machine 1

    ```
    scp ~/tls-gen/basic/result/ca_certificate.pem <username>@<hostname or ip of machine1>:<path on machine1>
    ```

2. Concatenate CA certificate of remote machine with the one on the local machine. On machine1 (volttron machine) the certificate of machine2 should be added to <instance_name>-trusted-cas.crt. On machine2 the certificate of machine1 should be appened to ~/tls-gen/basic/result/ca-certificate.pem

    For example:

    On machine 1: cat <path used in the second scp command above>/ca_certificate.pem >> $VOLTTRON_HOME/certificates/certs/v1-trusted-cas.crt

    On machine 2: cat /tmp/v1-root-ca.crt >> ~/tls-gen/basic/result/ca-certificate.pem

3. Restart RabbitMQ brokers on both machines. Repeat the following command on both machines
    ```
   ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl stop
   ~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmq-server -detached
    ```

4. On machine 1, modify Listener agent to subscribe to all topics from all pathforms. Open the file <volttron_source_home>/examples/ListenerAgent/listener/agent.py.
Search for @PubSub.subscribe('pubsub', '') and replace that line with @PubSub.subscribe('pubsub', 'devices', all_platforms=True)

5. Install listener agent and master driver agent with a fake device and restart VOLTTRON. Start both agents

    ```
    ./stop-volttron
    vcfg --agent master_driver
    ./start-volttron
    vctl start --tag master_driver
    scripts/core/upgrade-listener
    ```

6. On machine 2, modify config to point to path of 'test-admin' client certificates. Set the hostname, amqps port and virtual host of remote VOLTTRON instance running on machine 1.

    ca_certfile: "path to self signed CA certificate"

    client_public_cert: "path to public certificate of test-admin"

    client_private_cert: "path to private certificate of test-admin"

7. On machine 2, create federation link to upstream RabbitMQ broker.
```
python create_parameter.py create federation
```

8. Start the client program. The federation status is not shown if there are no subscribers bound to the 'volttron' exchange.
```
python rabbitmq_gevent_publisher.py
```

9. Check the federation status. 
```
~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl eval 'rabbit_federation_status:status().'
```

10. On machine 2, Create user 'test-admin' to get access to the VOLTTRON instance on machine 1.
```
volttron-ctl rabbitmq add-user test-admin default
Do you want to set READ permission  [Y/n]
Do you want to set WRITE permission  [Y/n]
Do you want to set CONFIGURE permission  [Y/n]
```

11. You should start seeing device data being received on the machine 2.

On machine 2:
```
Incoming message from local RabbitMQ publisher. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
Publishing to topic: __pubsub__.test.hello.volttron, i:19
Incoming message from local RabbitMQ publisher. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
Incoming message from VOLTTRON. Topic:__pubsub__.collector1.devices.fake-campus.fake-building.fake-device.all.#    Message: {"headers":{"Date":"2019-08-20T02:48:00.002375+00:00","TimeStamp":"2019-08-20T02:48:00.002375+00:00","min_compatible_version":"5.0","max_compatible_version":"","SynchronizedTimeStamp":"2019-08-20T02:48:00.000000+00:00"},"message":[{"Heartbeat":true,"PowerState":0,"temperature":50.0,"ValveState":0},{"Heartbeat":{"units":"On/Off","tz":"US/Pacific","type":"integer"},"PowerState":{"units":"1/0","tz":"US/Pacific","type":"integer"},"temperature":{"units":"Fahrenheit","tz":"US/Pacific","type":"integer"},"ValveState":{"units":"1/0","tz":"US/Pacific","type":"integer"}}],"sender":"platform.driver","bus":""}
```

12. To get messages published by RabbitMQ client on machine 2 into VOLTTRON on machine 1, we need to create a federation
link to upstream server (machine 2) on machine 1. We can use VOLTTRON 'volttron-ctl' utility command to it.

On machine 1:

```
vcfg --rabbitmq federation [optional path to rabbitmq_federation_config.yml
containing the details of the upstream (machine2) hostname, port and vhost.]
```

13. Create user <instance_name>-admin to get access to virtual host 'test' on machine 2.

```
~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl add_user v1-admin default
~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl set_permissions v1-admin ".*" ".*" ".*"
```
Here we assume, 'v1' is instance name of VOLTTRON instance running on machine 1.

14. You should start seeing messages with 'hello' topic in the VOLTTRON logs now.

On machine 1:
```
2019-08-19 19:52:25,016 (listeneragent-3.2 10844) listener.agent INFO: Peer: pubsub, Sender: test-admin:, Bus: test, Topic: hello, Headers: {'max_compatible_version': '0.5', 'min_compatible_version': '0.1'}, Message: 
'Hello from NON volttron client'
```

15. To delete the federation link to upstream server on machine 1.

On machine 2:

```
python create_parameter.py delete federation
```

15. To delete the federation link to upstream server on machine 2, use 'volttron-ctl' utility command.

On machine 1,

a. Get the federation upstream parameter nam
```
vctl rabbitmq list-federation-parameters
```

b. Grab the upstream link name and run the below command to remove it.
```
vctl rabbitmq remove-federation-parameters upstream-volttron2-rabbit-2
```

## Shovel Setup:

1. Make sure root CA certificates are copied over and concatenated to local root CA certificates so that RabbitMQ broker
can trust them. Also install master driver and listener agents on machine 1. Follow steps 1-6 of Federation Setup section.

2. To create a shovel link to send messages from machine 2 to machine 1, configure shovel options in config file to point to hostname,
port and virtual host of machine 1 and then create shovel parameter.

On machine 2, 
```
cd ~/external-clients-for-rabbitmq/python-rabbitmq-volttron-client
```

Update shovel parameters (hostname, port) in the config file.
```
python create_parameter.py create shovel
```

3. Run the test client program. The shovel will forward 'hello' messages from the test program to VOLTTRON instance on machine 1.
```
python rabbitmq_gevent_publisher.py
```

4. Create user 'test-admin' to get access to the VOLTTRON instance on machine 1.
```
volttron-ctl rabbitmq add-user test-admin default
Do you want to set READ permission  [Y/n]
Do you want to set WRITE permission  [Y/n]
Do you want to set CONFIGURE permission  [Y/n]
```

5. You should see hello messages being received on the machine 1.

On machine 1:
```
2019-08-20 10:46:07,281 (listeneragent-3.2 10844) listener.agent INFO: Peer: pubsub, Sender: test-admin:, Bus: test, Topic: hello, Headers: {'max_compatible_version': '0.5', 'min_compatible_version': '0.1'}, Message: 
'Hello from NON volttron client'
```

6. To create a shovel connection to forward messages with 'devices' topic from master driver agent running on machine 1 to the test program on machine 2.

On machine, use 'volttron-cfg ' utility command

```
(volttron)nidd494@node-zmq:~/volttron$ vcfg --rabbitmq shovel

Your VOLTTRON_HOME currently set to: /home/nidd494/.volttron

Is this the volttron you are attempting to setup? [Y]: 
Name of this volttron instance: [collector1]: 
Number of destination hosts to configure: [1]: 
Hostname of the destination server:  central
Port of the destination server:  [5671]: 
Virtual host of the destination server:  [volttron]: test

Do you want shovels for PUBSUB communication?  [N]: y
Name of the agent publishing the topic: platform.driver
List of PUBSUB topics to publish to this remote instance (comma seperated) devices

Do you want shovels for RPC communication?  [N]: n
2019-08-20 10:49:31,479 volttron.utils.rmq_mgmt DEBUG: Create READ, WRITE and CONFIGURE permissions for the user: collector1.platform.driver
2019-08-20 10:49:31,590 volttron.utils.rmq_mgmt DEBUG: Create READ, WRITE and CONFIGURE permissions for the user: collector1.platform.driver
```

7. Add user <instance_name>-platform.driver to get access to virtual host 'test' on machine 2.

On machine 2,

```
~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl add_user v1.platform.driver default
~/rabbitmq_server/rabbitmq_server-3.7.7/sbin/rabbitmqctl -p test set_permissions v1.platform.driver ".*" ".*" ".*"
```
Here we assume, 'v1' is instance name of VOLTTRON instance running on machine 1.

8. You should start seeing messages for 'devices' topic on machine 2.

```
Incoming message from VOLTTRON. Topic:__pubsub__.test.hello.volttron    Message: {"bus": "test", "message": "Hello from NON volttron client", "sender": "test-admin", "headers": {"max_compatible_version": "0.5", "min_compatible_version": "0.1"}}
Incoming message from local RabbitMQ publisher. Topic:__pubsub__.collector1.devices.fake-campus.fake-building.fake-device.all.#    Message: {"headers":{"Date":"2019-08-20T17:52:05.001937+00:00","TimeStamp":"2019-08-20T17:52:05.001937+00:00","min_compatible_version":"5.0","max_compatible_version":"","SynchronizedTimeStamp":"2019-08-20T17:52:05.000000+00:00"},"message":[{"Heartbeat":true,"PowerState":0,"temperature":50.0,"ValveState":0},{"Heartbeat":{"units":"On/Off","tz":"US/Pacific","type":"integer"},"PowerState":{"units":"1/0","tz":"US/Pacific","type":"integer"},"temperature":{"units":"Fahrenheit","tz":"US/Pacific","type":"integer"},"ValveState":{"units":"1/0","tz":"US/Pacific","type":"integer"}}],"sender":"platform.driver","bus":""}
```

9. To delete the shovel link to machine 1.

On machine 2,
```
python create_parameter.py delete shovel
```

10. To delete the shovel link to machine 2, use 'volttron-ctl' utility command.

On machine 1,

a. Get the federation upstream parameter nam
```
vctl rabbitmq list-shovel-parameters
```

b. Grab the shovel link name and run the below command to remove it.
```
vctl rabbitmq remove-shovel-parameters shovel-central-devices
```
