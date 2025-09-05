import pulumi
import pulumi_aws as aws

def create_security_groups(vpc, public_subnet, private_subnet):
    """Create security groups for each component"""

    bastion_security_group = aws.ec2.SecurityGroup(
        resource_name='bastion-security-group',
        vpc_id=vpc.id,
        description="Security group for Bastion",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol='tcp',
                from_port=22,
                to_port=22,
                cidr_blocks=['0.0.0.0/0']
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol='-1',
                from_port=0,
                to_port=0,
                cidr_blocks=['0.0.0.0/0']
            )
        ],
        tags={'Name': 'bastion-security-group'}
    )


    db_security_group = aws.ec2.SecurityGroup(
        resource_name='db-security-group',
        vpc_id=vpc.id,
        description='Security group for MySQL database',
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol='tcp',
                from_port=22,
                to_port=22,
                security_groups=[bastion_security_group.id]
            ),
            aws.ec2.SecurityGroupIngressArgs(
                protocol='tcp',
                from_port=3306,
                to_port=3306,
                security_groups=[bastion_security_group.id]
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol='-1',
                from_port=0,
                to_port=0,
                cidr_blocks=['0.0.0.0/0']
            )
        ],
        tags={'Name': 'db-security-group'}
    )


    return {
        "bastion": bastion_security_group,
        "db": db_security_group
    }