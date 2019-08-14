import requests
import json
import argparse
import os
import yaml

def build_ssl_params(config_params):
    ssl_params = None
    try:
        ca_file = config_params['ca_certfile']
        cert_file = config_params['client_public_cert']
        key_file = config_params['client_private_cert']
        ssl_params = "cacertfile={ca}&certfile={cert}&keyfile={key}" \
                     "&verify=verify_peer&fail_if_no_peer_cert=true" \
                     "&auth_mechanism=external".format(ca=ca_file,
                                                       cert=cert_file,
                                                       key=key_file)
    except KeyError as e:
        print("Missing SSL options in config: {}".format(e))
    return ssl_params


def get_common_params(config_params):
    common_params = dict()
    try:
        local_host = config_params['host']
        local_amqps_port = config_params['amqps_port']
        local_vhost = config_params['virtual_host']
        https_port = 15671
        admin_user = config_params['user']
        admin_passwd = config_params['password']
        ca_file = config_params['ca_certfile']
        cert_file = config_params['client_public_cert']
        key_file = config_params['client_private_cert']
        return local_host, local_amqps_port, https_port, local_vhost, \
               admin_user, admin_passwd, ca_file, cert_file, key_file
    except KeyError as e:
        print("Missing key: {}".format(e))
        raise


def create_federation_setup(config_params):
    """
    Create Federation link with upstream (VOLTTRON instance)
    :param config_params: configuration parameters
    :return:
    """
    upstream_name = "non-volttron-federation"
    try:
        local_host, local_amqps_port, https_port, local_vhost, admin_user, \
        admin_passwd, ca_file, cert_file, key_file = get_common_params(config_params)
    except KeyError:
        return

    ssl_params = build_ssl_params(config_params)
    remote_host = config_params['federation']['remote_host']
    remote_amqps_port = config_params['federation']['remote_amqps_port']
    remote_vhost = config_params['federation']['remote_virtual_host']

    # Build upstream RabbitMQ address
    remote_rmq_address = "amqps://{host}:{port}/{vhost}?" \
                  "{ssl_params}&server_name_indication={host}".format(
        host=remote_host,
        port=remote_amqps_port,
        vhost=remote_vhost,
        ssl_params=ssl_params)

    # Set upstream parameter
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
    # Set policy to make local exchange 'federated'.
    # Note, exchange by name 'volttron' should already exist
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
    """
    Create shovel link with remote server (VOLTTRON instance)
    :param config_params: configuration parameters
    :return:
    """
    shovel_name = "non-volttron-shovel"
    try:
        local_host, local_amqps_port, https_port, local_vhost, admin_user, \
        admin_passwd, ca_file, cert_file, key_file = get_common_params(config_params)
    except KeyError:
        return

    remote_host = config_params['shovel']['remote_host']
    remote_amqps_port = config_params['shovel']['remote_amqps_port']
    remote_vhost = config_params['shovel']['remote_virtual_host']

    ssl_params = "cacertfile={ca}&certfile={cert}&keyfile={key}" \
                 "&verify=verify_peer&fail_if_no_peer_cert=true" \
                 "&auth_mechanism=external".format(ca=ca_file,
                                                   cert=cert_file,
                                                   key=key_file)

    # Build source (local) RabbitMQ address
    src_uri = "amqps://{host}:{port}/{vhost}?" \
                  "{ssl_params}&server_name_indication={host}".format(
        host=local_host,
        port=local_amqps_port,
        vhost=local_vhost,
        ssl_params=ssl_params)

    # Build destination (VOLTTRON) RabbitMQ address
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


def delete_parameter(component, config_params):
    """
    Delete federation/Shovel link
    :param component: 'federation-upstream' or 'shovel'
    :param config_params: configuration parameters
    :return:
    """
    local_vhost = config_params['virtual_host']
    ca_file = config_params['ca_certfile']
    cert_file = config_params['client_public_cert']
    key_file = config_params['client_private_cert']
    local_host = config_params['host']
    admin_user = config_params['user']
    admin_passwd = config_params['password']

    if component == 'federation':
        component = 'federation-upstream'
    prefix='https://{host}:{port}'.format(host=local_host, port=15671)
    url = '{prefix}/api/parameters/{component}/{vhost}'.format(prefix=prefix,component=component,vhost=local_vhost)

    # Get all parameters based on component type
    response = requests.get(url,
                            headers={"Content-Type": "application/json"},
                            auth=(admin_user, admin_passwd),
                            verify=ca_file,
                            cert=(cert_file, key_file))
    params = [p['name'] for p in response.json()]

    for p in params:
        # Delete parameter
        url = '{prefix}/api/parameters/{component}/{vhost}/{param}'.format(prefix=prefix,
                                                                           component=component,
                                                                           vhost=local_vhost,
                                                                           param=p)
        req = requests.delete(url=url, headers={"Content-Type": "application/json"}, auth=(admin_user, admin_passwd),
                              verify=ca_file, cert=(cert_file, key_file))
        print(req.status_code)

    if component == 'federation-upstream':
        # Delete policy as well
        url = '{prefix}/api/policies/{vhost}'.format(prefix=prefix, vhost=local_vhost)
        response = requests.get(url,
                                headers={"Content-Type": "application/json"},
                                auth=(admin_user, admin_passwd), verify=ca_file, cert=(cert_file, key_file))
        policies = [p['name'] for p in response.json()]
        for p in policies:
            url = '{prefix}/api/policies/{vhost}/{name}'.format(prefix=prefix,
                                                                vhost=local_vhost,
                                                                name=p)
            req = requests.delete(url=url, headers={"Content-Type": "application/json"},
                                  auth=(admin_user, admin_passwd),
                                  verify=ca_file, cert=(cert_file, key_file))
            print(req.status_code)


if __name__ == '__main__':
    # Entry point for script
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("op")
        parser.add_argument("type")
        args = parser.parse_args()
        print(args.type)
        config_opts = None
        config_path = os.path.join(os.getcwd(), 'config')

        with open(config_path, 'r') as yaml_file:
            config_opts = yaml.load(yaml_file)
        if args.op == 'create':
            if args.type == 'federation':
                create_federation_setup(config_opts)
            elif args.type == 'shovel':
                create_shovel_setup(config_opts)
        elif args.op == 'delete':
            delete_parameter(args.type, config_opts)
    except KeyboardInterrupt:
        pass
