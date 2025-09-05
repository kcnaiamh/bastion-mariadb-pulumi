import pulumi
import pulumi_aws as aws
from utils import read_file, gen_password

def create_instances(network, security_groups, config):
    """Create EC2 instances for each component"""

    DB_NAME = config["db_name"]
    DB_USER = config["db_user"]
    DB_PASS = config["db_pass"]
    SSH_KEY_NAME = config["ssh_key_name"]
    aws_key = config["aws_key"]
    REGION_NAME = aws.get_region().name

    # Read script files
    mysql_setup_script = read_file('scripts/mysql/mysql-setup.sh')
    db_schema = read_file('scripts/mysql/schema.sql')
    bastion_setup_script = read_file('scripts/bastion/bastion-setup.sh')


    def generate_mysql_user_data():
        return f'''\
#!/usr/bin/env bash
set -euxo pipefail
exec > >(tee /var/log/mariadb-userdata.log) 2>&1

sed -i 's|URIs: http://ap-southeast-1.ec2.archive.ubuntu.com/ubuntu/|URIs: https://mirror.xeonbd.com/ubuntu-archive/|g' /etc/apt/sources.list.d/ubuntu.sources

echo "DB_ROOT_PASS={gen_password(12)}" >> /etc/environment
echo "DB_NAME={DB_NAME}" >> /etc/environment
echo "DB_USER={DB_USER}" >> /etc/environment
echo "DB_PASS={DB_PASS}" >> /etc/environment

apt update

mkdir -p /usr/local/bin


cat > /usr/local/bin/mysql-setup.sh << 'FINAL'
{mysql_setup_script}
FINAL

cat > /tmp/schema.sql << 'EOF'
{db_schema}
EOF

chmod +x /usr/local/bin/mysql-setup.sh


/usr/local/bin/mysql-setup.sh && \
rm /usr/local/bin/mysql-setup.sh
'''

    db = aws.ec2.Instance(
        resource_name = 'db-server',
        instance_type = 't2.micro',
        ami = 'ami-01811d4912b4ccb26',
        subnet_id = network["private_subnet"].id,
        key_name = SSH_KEY_NAME,
        vpc_security_group_ids=[
            security_groups["db"].id
        ],
        user_data=generate_mysql_user_data(),
        user_data_replace_on_change=True,
        tags = {
            'Name': 'db-server'
        },
        opts=pulumi.ResourceOptions(
            depends_on=[
                network["nat_gateway"],
                network["private_route_table_association"],
                network["private_subnet"]
            ] + ([aws_key] if aws_key else [])
        )
    )



    def generate_bastion_user_data():
        return f'''\
#!/usr/bin/env bash
set -euxo pipefail
exec > >(tee /var/log/bastion-userdata.log) 2>&1

sed -i 's|URIs: http://ap-southeast-1.ec2.archive.ubuntu.com/ubuntu/|URIs: https://mirror.xeonbd.com/ubuntu-archive/|g' /etc/apt/sources.list.d/ubuntu.sources

apt update

mkdir -p /usr/local/bin
mkdir -p /opt/app

cat > /usr/local/bin/bastion-setup.sh << 'EOF'
{bastion_setup_script}
EOF

chmod +x /usr/local/bin/bastion-setup.sh

/usr/local/bin/bastion-setup.sh
'''

    bastion = aws.ec2.Instance(
        resource_name='bastion-server',
        instance_type='t2.micro',
        ami='ami-01811d4912b4ccb26',
        subnet_id=network["public_subnet"].id,
        key_name=SSH_KEY_NAME,
        vpc_security_group_ids=[
            security_groups["bastion"].id
        ],
        associate_public_ip_address=True,
        user_data=generate_bastion_user_data(),
        user_data_replace_on_change=True,
        tags={
            'Name': 'bastion-server'
        },
        opts=pulumi.ResourceOptions(
            depends_on=[] + ([aws_key] if aws_key else [])
        )
    )

    return {
        "bastion": bastion,
        "db": db
    }