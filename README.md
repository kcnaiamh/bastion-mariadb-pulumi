## Project Overview

This project automates the provisioning of a secure AWS infrastructure using Pulumi with Python and integrates multiple components such as:

- **Provision AWS infrastructure** through Pulumi
- **Secure access to MariaDB** through Bastion server.
- **Automated setup and configuration** via bash scripts.

The primary goal is to create a robust, automated, and secure deployment solution with IaC that minimizes manual intervention and enforces best practices with security in mind.

## Architecture

This is the top level overview of the whole infrastructure that the code will build.

## Technologies Used

- **Programming & Scripting Languages:**

  - Python (Pulumi scripts)
  - Bash (Setup and configuration scripts)
  - SQL (Provision Database)

- **Infrastructure & Cloud Services:**

  - Pulumi with the `pulumi-aws`, `pulumi-tls` provider
  - Amazon Web Services (AWS): EC2, VPC, Subnets, NAT Gateway, Internet Gateway, etc.

- **Databases & Data Stores:**

  - MariaDB (Database server)

## Prerequisites

Before running the project, ensure you have:

- **AWS Account** with proper permissions and balance.
- **Pulumi CLI** installed.
- **AWS CLI** installed and configured with access and secret token.

## Deployment & Execution

**Attention**: Make sure you have all the prerequisites mentioned previously before proceeding for deployment.

To deploy the infrastructure and services you just need to run 2 commands.

1. **Use The Template**. Yes, this repo is actually a Pulumi template. You can directly setup you project just running the following command in an **empty directory**.

   ```
   pulumi new https://github.com/kcnaiamh/bastion-mariadb-pulumi
   ```

   ![[Pasted image 20250905162411.png]]

1. **Run Pulumi Up**. This command will provision the AWS resources as defined in `__main__.py`.

   ```
   pulumi up --yes
   ```

   ![[Pasted image 20250905152224.png]]

   It will take 3/4 minute for provisioning the AWS infrastructure.

   Now to get into bastion server just run `ssh bastion-server` in your terminal.

   ![[Pasted image 20250905152656.png]]

   Also, to get into database server run `ssh db-server` in your another terminal.

   ![[Pasted image 20250905152807.png]]

1. **Do the Cleanup**. Run `pulumi destroy --yes --remove` to delete the whole infrastructure. (Be cautious about AWS bill.)

   ![[Pasted image 20250905155030.png]]

## Security Considerations

- **Sensitive Data:** Environment variables and configuration files may contain sensitive data such as database passwords and API tokens. **Secure these files and manage permissions carefully.** Keep in mind that, by default, any user can read the `/etc/environment` file, so avoid storing sensitive credentials there. Even if you use if for automation, remove it in the process of last clean-up process in automation script (**advice to future me :)**).

- **Service Hardening:** Systemd services are configured to automatically restart upon failure, ensuring service continuity. **Use the least privilege principle for sensitive files, especially scripts executed by systemd or cron jobs running as a privileged user.** Regularly update and patch all installed packages. Additionally, note that the default user in an EC2 instance can use the `sudo` binary without a password. **For added security, consider enforcing password authentication for sudo access.**

- **Communication Security:** Always use secure communication channels such as HTTPS and SSH where possible. **Avoid exposing sensitive ports to the public internet.** In this project, created a new user for bastion server and configured ssh daemon in database to only connect from bastion server `ops` user and MaridaDB to listen on only specific interface (Private IP).

## Troubleshooting & Maintenance

- **Pulumi Deployment Issues:**

  - Check Pulumi logs for errors.
  - Ensure that AWS credentials and configurations are correct.

- **Script Failures:**

  - Examine log outputs (e.g., `/var/log/mysql-setup.log`, `/var/log/mysql-userdata.log`,  `/var/log/bastion-setup.log`, `/var/log/bastion-userdata.log`) for error messages.
  - Validate that all required environment variables are properly set.

## Challenges and Solutions

During the automation process, I encountered several challenges. In this section, I'll highlight the most significant ones and how I resolved them.

1.  **APT not working**

    It was for 2 reasons:

    - Database EC2 instance was provisioned before NAT gateway and other components. That's why the configuration bash script was failing as it can not get internet connection.
    - For some reason Ubuntu mirror for AWS ap-southeast-1 region was not working. That's why I changed the mirror location.

2.  **Logging**

    Debugging automation failures is crucial, especially when scripts crash. To improve visibility, I enabled detailed logging in every Bash script by using:

    ```shell
    exec > >(tee -a /var/log/logfile.log) 2>&1
    set -euxo pipefail
    ```

    This setup ensures that:

    - Every command and its output are logged to `/var/log/logfile.log`.
    - Pipelines fail if any command within them fails (`set -o pipefail`).
    - Undefined variables trigger an error (`set -u`).
    - Errors cause immediate script termination (`set -e`).

---

## Some Other Screenshots

```
pulumi stack output
```

![[Pasted image 20250905152447.png]]

```
systemctl status mariadb
```

![[Pasted image 20250905152916.png]]

```
mysql -h <db-private-ip> -u appuser -p -e "SHOW DATABASES;"
```

![[Pasted image 20250905153015.png]]

---

## Setup Without Pulumi Template

If you want to clone the git repo and want to configure it manually then following this instruction:

1. Clone the git repo.

   ```
   git clone https://github.com/kcnaiamh/bastion-mariadb-pulumi
   ```

2. Remove `.example` from `Pulumi.dev.yaml.example` file name.
3. Setup python virtual environment. (assuming linux environment)
   ```
   python3 -m venv venv
   source ./venv/bin/activate
   pip install -r requirements.txt
   ```
4. Setup AWS configuration.
   ```
   aws configure
   ```
5. Create a stack name `dev` (assuming `dev` stack not exist yet)
   ```
   pulumi stack init dev
   ```
6. Configure stack settings
   ```
   pulumi config set aws:region ap-southeast-1
   pulumi config set demo-project-3:dbName appdb
   pulumi config set demo-project-3:dbUser appuser
   pulumi config set --secret demo-project-3:dbPass Abcd!234
   pulumi config set demo-project-3:sshKeyName master-key
   ```
   Here, `demo-project-3` is the name of the project that is specified in `Pulumi.yaml` file.
7. Dry run the code
   ```
   pulumi preview
   ```
8. Deploy it
   ```
   pulumi up -y
   ```
