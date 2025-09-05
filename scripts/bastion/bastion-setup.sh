#!/usr/bin/env bash

# Exit on error, trace commands, don't allow unset variables,
# pileline status code is 0 iff all commands in pipeline has status code 0
set -euxo pipefail
exec > >(tee -a "/var/log/bastion-setup.log") 2>&1

echo "Starting NodeJS setup at $(date)"

source /etc/environment

# Main script execution
function main() {
    # apt update
    apt install -y netcat-openbsd curl mariadb-client

    # Create dedicated user for running the application
    if ! id -u ops &>/dev/null; then
        useradd -m -s /bin/bash ops

        echo "ops ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ops
        chmod 440 /etc/sudoers.d/ops

        mkdir -p /home/ops/.ssh
        cp /home/ubuntu/.ssh/authorized_keys /home/ops/.ssh/authorized_keys

        chown -R ops:ops /home/ops/.ssh
        chmod 700 /home/ops/.ssh
        chmod 600 /home/ops/.ssh/authorized_keys
    fi

    # A backup of the original config is created before modification.
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

    # Disable PermitRootLogin
    sed -i 's/^#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    if ! grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
        echo "PermitRootLogin no" >> /etc/ssh/sshd_config
    fi

    # Disable PasswordAuthentication
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    if ! grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
        echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
    fi

    # Allow only ops user to login
    echo "AllowUsers ops" >> /etc/ssh/sshd_config

    systemctl restart ssh


    echo "NodeJS setup completed successfully at $(date)"
}

main
