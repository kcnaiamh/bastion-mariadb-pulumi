#!/usr/bin/env bash
# Exit on error, trace commands, don't allow unset variables,
# pipeline status code is 0 iff all commands in pipeline has status code 0
set -euxo pipefail
exec > >(tee -a /var/log/mariadb-setup.log) 2>&1

echo "Starting MariaDB setup at $(date)"

source /etc/environment

# MariaDB Configurations
DB_ROOT_PASS="${DB_ROOT_PASS}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASS="${DB_PASS}"

# Install MariaDB
apt update
apt install -y mariadb-server

# Ensure MariaDB is running
if ! systemctl is-active --quiet mariadb.service; then
    echo 'MariaDB server is not running. Starting MariaDB server...'
    systemctl enable --now mariadb
fi

# ---------------------------------------------------------------------------- #
# CONFIGURE FOR REMOTE ACCESS
# ---------------------------------------------------------------------------- #
echo "Configuring MariaDB for remote access..."
PRIVATE_IP=$(ip -4 -o addr show | awk '!/127.0.0.1/ {print $4}' | cut -d/ -f1 | head -n 1)
sed -i "s/^bind-address.*/bind-address = ${PRIVATE_IP}/g" /etc/mysql/mariadb.conf.d/50-server.cnf
systemctl restart mariadb

# ---------------------------------------------------------------------------- #
# SET DATABASE ROOT USER PASSWORD
# ---------------------------------------------------------------------------- #
mysql --user=root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
EOF

# Save root credentials for automation
cat > /root/.my.cnf <<EOF
[client]
user=root
password="${DB_ROOT_PASS}"
EOF
chmod 600 /root/.my.cnf

# ---------------------------------------------------------------------------- #
# SECURE INSTALLATION EQUIVALENT
# ---------------------------------------------------------------------------- #
mysql --defaults-file=/root/.my.cnf <<EOF
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test';
FLUSH PRIVILEGES;
EOF

# ---------------------------------------------------------------------------- #
# USER CREATION & PERMISSION SETUP
# ---------------------------------------------------------------------------- #
mysql --defaults-file=/root/.my.cnf <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASS}';
GRANT SELECT, INSERT, UPDATE, GRANT OPTION ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
EOF

# ---------------------------------------------------------------------------- #
# RUN schema.sql TO CREATE DATABASE SCHEMA
# ---------------------------------------------------------------------------- #
if [ -f /tmp/schema.sql ]; then
    mysql --defaults-file=/root/.my.cnf --database="${DB_NAME}" < /tmp/schema.sql
    rm -f /tmp/schema.sql
fi

echo "MariaDB setup completed successfully at $(date)"
