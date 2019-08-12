import requests
import json
import argparse
import os
import yaml

ca_file = "/home/nidd494/tls-gen/basic/result/ca_certificate.pem"
cert_file = "/home/nidd494/tls-gen/basic/result/client_certificate.pem"
key_file = "/home/nidd494/tls-gen/basic/result/client_key.pem"
host='central'
port=15671

def add_vhost(virtual_host='volttron'):
    global host, port, ca_file
    url = "https://{host}:{port}/api/vhosts/{vhost}".format(host=host, port=port, vhost=virtual_host)
    req = requests.put(url, headers={"Content-Type": "application/json"},
                       auth=('rabbit-1', 'default'), verify=ca_file, cert=(cert_file, key_file))
    print(req.status_code)


def add_user(new_user, password, vhost):
    tags='administrator'
    body = dict(password=password, tags=tags)

    url = 'https://{host}:{port}/api/users/{user}'.format(host=host, port=port, user=new_user)
    response = requests.put(url, url, data=json.dumps(body), headers={"Content-Type": "application/json"},
                       auth=('rabbit-1', 'default'), verify=ca_file, cert=(cert_file, key_file))

    permissions = {"configure": ".*", "write": ".*", "read": ".*"}
    url = '/api/permissions/{vhost}/{user}'.format(vhost=vhost, user=new_user)
    response = requests.put(url, url, data=json.dumps(body), headers={"Content-Type": "application/json"},
                            auth=('rabbit-1', 'default'), verify=ca_file, cert=(cert_file, key_file))
    print(response.status_code)


def create_federation_setup(config_params):
    upstream_name = "non-volttron-federation"
    ca_file = config_params['ca_certfile']
    cert_file = config_params['client_public_cert']
    key_file = config_params['client_private_cert']

    remote_host = config_params['federation']['remote_host']
    remote_amqps_port = config_params['federation']['remote_amqps_port']
    remote_vhost = config_params['federation']['remote_virtual_host']
    local_host = config_params['host']
    local_vhost = config_params['virtual_host']
    https_port = 15671
    admin_user = config_params['user']
    admin_passwd = config_params['password']
    ssl_params = "cacertfile={ca}&certfile={cert}&keyfile={key}" \
                 "&verify=verify_peer&fail_if_no_peer_cert=true" \
                 "&auth_mechanism=external".format(ca=ca_file,
                                                   cert=cert_file,
                                                   key=key_file)
    remote_rmq_address = "amqps://{host}:{port}/{vhost}?" \
                  "{ssl_params}&server_name_indication={host}".format(
        host=remote_host,
        port=remote_amqps_port,
        vhost=remote_vhost,
        ssl_params=ssl_params)

    # Set parameter
    body = dict(vhost=local_vhost,
                component="federation-upstream",
                name=upstream_name,
                value={"uri": remote_rmq_address})
    url = 'https://{host}:{port}/api/parameters/{component}/{vhost}/{param}'.format(host=local_host,
                                                                                    port=https_port,
                                                                                    component="federation-upstream",
                                                                                    vhost=local_vhost,
                                                                                    param=upstream_name)
    print("Creating Upstream parameter: {}".format(upstream_name))
    req = requests.put(url, data=json.dumps(body), headers={"Content-Type": "application/json"},
                       auth=(admin_user, admin_passwd), verify=ca_file, cert=(cert_file, key_file))
    print(req.status_code)
    # Set policy
    policy_name = "non-volttron-federation"
    policy_value = {"pattern": "^volttron",
                    "definition": {"federation-upstream-set": "all"},
                    "priority": 0,
                    "apply-to": "exchanges"}

    url = 'https://{host}:{port}/api/policies/{vhost}/{name}'.format(host=local_host, port=https_port,
                                                                     vhost=local_vhost, name=policy_name)
    print("Creating Federation policy: {}".format(policy_name))
    req = requests.put(url, data=json.dumps(policy_value),
                       headers={"Content-Type": "application/json"},
                       auth=(admin_user, admin_passwd), verify=ca_file, cert=(cert_file, key_file))
    print(req.status_code)


def create_shovel_setup(config_params):
    global host, port, ca_file
    shovel_name = "non-volttron-shovel"
    ca_file = config_params['ca_certfile']
    cert_file = config_params['client_public_cert']
    key_file = config_params['client_private_cert']

    remote_host = config_params['shovel']['remote_host']
    remote_amqps_port = config_params['shovel']['remote_amqps_port']
    remote_vhost = config_params['shovel']['remote_virtual_host']
    local_host = config_params['host']
    local_amqps_port = config_params['amqps_port']
    local_vhost = config_params['virtual_host']
    https_port = 15671
    admin_user = config_params['user']
    admin_passwd = config_params['password']

    ssl_params = "cacertfile={ca}&certfile={cert}&keyfile={key}" \
                 "&verify=verify_peer&fail_if_no_peer_cert=true" \
                 "&auth_mechanism=external".format(ca=ca_file,
                                                   cert=cert_file,
                                                   key=key_file)

    src_uri = "amqps://{host}:{port}/{vhost}?" \
                  "{ssl_params}&server_name_indication={host}".format(
        host=local_host,
        port=local_amqps_port,
        vhost=local_vhost,
        ssl_params=ssl_params)

    dest_uri = "amqps://{host}:{port}/{vhost}?" \
                  "{ssl_params}&server_name_indication={host}".format(
        host=remote_host,
        port=remote_amqps_port,
        vhost=remote_vhost,
        ssl_params=ssl_params)

    routing_key = config_params['shovel']['publish_topic']
    body = dict(vhost=local_vhost,
                component="shovel",
                name=shovel_name,
                value={"src-uri": src_uri,
                       "src-exchange": "volttron",
                       "src-exchange-key": routing_key,
                       "dest-uri": dest_uri,
                       "dest-exchange": "volttron"}
                )

    url = 'https://{host}:{port}/api/parameters/{component}/{vhost}/{param}'.format(host=local_host,
                                                                                    port=https_port,
                                                                                    component="shovel",
                                                                                    vhost=local_vhost,
                                                                                    param=shovel_name)
    print("Creating shovel parameter: {}".format(shovel_name))
    req = requests.put(url, data=json.dumps(body), headers={"Content-Type": "application/json"},
                       auth=(admin_user, admin_passwd), verify=ca_file, cert=(cert_file, key_file))
    print(req.status_code)

if __name__ == '__main__':
    # Entry point for script
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("type")
        args = parser.parse_args()
        print(args.type)
        config_opts = None
        config_path = os.path.join(os.getcwd(), 'config')

        with open(config_path, 'r') as yaml_file:
            config_opts = yaml.load(yaml_file)
        if args.type == 'federation':
            create_federation_setup(config_opts)
        elif args.type == 'shovel':
            create_shovel_setup(config_opts)
    except KeyboardInterrupt:
        pass
