import pulumi
from network import create_network_infrastructure
from security import create_security_groups
from instances import create_instances
from utils import create_ssh_key, create_config_file

# Configuration
config = pulumi.Config()
DB_NAME = config.require("dbName")
DB_USER = config.require("dbUser")
DB_PASS = config.require("dbPass")
SSH_KEY_NAME = config.require("sshKeyName")

# Create infrastructure components
aws_key = create_ssh_key(SSH_KEY_NAME)

network = create_network_infrastructure()
vpc = network["vpc"]
public_subnet = network["public_subnet"]
private_subnet = network["private_subnet"]

security = create_security_groups(vpc, public_subnet, private_subnet)

instances = create_instances(
    network=network,
    security_groups=security,
    config={
        "db_name": DB_NAME,
        "db_user": DB_USER,
        "db_pass": DB_PASS,
        "ssh_key_name": SSH_KEY_NAME,
        "aws_key": aws_key
    }
)

# Export results
create_config_file(instances, SSH_KEY_NAME)
pulumi.export("bastion public ip:", instances['bastion'].public_ip)