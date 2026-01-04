# GOAD OpenStack Infrastructure

This OpenTofu/Terraform configuration deploys multiple instances of the GOAD (Game of Active Directory) penetration testing lab on OpenStack.

## Architecture

### Network Design
- **Management Network**: 10.200.0.0/24
  - Ubuntu deployment box: 10.200.0.250
  - Kali Linux box: 10.200.0.251

- **GOAD Instance Networks**: Each instance gets its own isolated subnet using standard GOAD IPs
  - All instances: 192.168.56.0/24 (isolated by OpenStack network)

### Per-Instance Layout
Each GOAD instance contains 5 Windows VMs using standard GOAD IP addresses:

| VM | Role | IP | Description |
|----|------|----|----|
| dc01 | Domain Controller | 192.168.56.10 | Primary DC for sevenkingdoms.local |
| dc02 | Domain Controller | 192.168.56.11 | DC for north.sevenkingdoms.local (child) |
| dc03 | Domain Controller | 192.168.56.12 | DC for essos.local |
| srv02 | Member Server | 192.168.56.22 | IIS, MSSQL, WebDAV server |
| srv03 | Member Server | 192.168.56.23 | MSSQL, WebDAV, ADCS server |

**Note**: All instances use the same IPs but in separate isolated networks

### Security Configuration
**IMPORTANT**: Security groups are **DISABLED** on all networks (`port_security_enabled = false`). This is required for network-based penetration testing attacks like:
- ARP spoofing
- LLMNR/NBT-NS poisoning
- SMB relay attacks
- MITM attacks

## Prerequisites

1. OpenStack credentials configured via environment variables:
   ```bash
   source ../app-cred-openrc.sh
   ```

2. OpenTofu or Terraform installed
   ```bash
   # Check installation
   tofu version
   # or
   terraform version
   ```

3. SSH keypair created in OpenStack
   ```bash
   # List your keypairs
   openstack keypair list

   # Create a new keypair if needed
   openstack keypair create --public-key ~/.ssh/id_rsa.pub my-keypair
   ```

## Available Resources

### Images
```bash
openstack image list
```
- WindowsServer2016, WindowsServer2019, WindowsServer2022, WindowsServer2025
- ubuntu-noble-server, ubuntu-jammy-server
- Kali2025

### Flavors
```bash
openstack flavor list
```
- **medium.6gb** (6GB RAM, 2 VCPUs) - Recommended for DCs and servers
- **medium** (4GB RAM, 2 VCPUs) - Suitable for Linux boxes
- **large.12gb** (12GB RAM, 4 VCPUs) - For resource-intensive scenarios

## Usage

### 1. Configure Variables

Copy the example configuration:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` to customize your deployment:
```hcl
# Deploy 2 complete GOAD instances (10 Windows VMs total)
goad_instance_count = 2

# Customize image names
windows_image_name = "WindowsServer2019"
ubuntu_image_name  = "ubuntu-noble-server"
kali_image_name    = "Kali2025"

# Customize flavors
dc_flavor_name     = "medium.6gb"
server_flavor_name = "medium.6gb"
linux_flavor_name  = "medium"

# Your SSH keypair
keypair = "your-keypair-name"
```

### 2. Initialize and Validate

```bash
# Source credentials
source ../app-cred-openrc.sh

# Initialize OpenTofu
tofu init

# Validate configuration
tofu validate

# Preview changes
tofu plan
```

### 3. Deploy Infrastructure

```bash
# Deploy with default settings (1 GOAD instance)
tofu apply

# Or deploy multiple instances
tofu apply -var="goad_instance_count=3"
```

### 4. Access Deployed Infrastructure

After deployment, view the outputs:
```bash
tofu output

# Get specific outputs
tofu output deployment_summary
tofu output all_floating_ips
tofu output ssh_commands
```

Example output:
```
ssh_commands = {
  "kali" = "ssh -i ~/.ssh/homefedora kali@129.21.x.x"
  "ubuntu" = "ssh -i ~/.ssh/homefedora ubuntu@129.21.x.x"
}
```

## Deployment Examples

### Small Lab (1 instance)
```bash
tofu apply -var="goad_instance_count=1"
```
- 5 Windows VMs (1 GOAD lab)
- 2 Linux boxes (Ubuntu + Kali)
- Total: 7 VMs

### Medium Lab (2 instances)
```bash
tofu apply -var="goad_instance_count=2"
```
- 10 Windows VMs (2 GOAD labs)
- 2 Linux boxes (Ubuntu + Kali)
- Total: 12 VMs

### Large Lab (3 instances)
```bash
tofu apply -var="goad_instance_count=3"
```
- 15 Windows VMs (3 GOAD labs)
- 2 Linux boxes (Ubuntu + Kali)
- Total: 17 VMs

### Massive Lab (30 instances)
```bash
tofu apply -var="goad_instance_count=30"
```
- 150 Windows VMs (30 GOAD labs)
- 2 Linux boxes (Ubuntu + Kali)
- Total: 152 VMs
- Networks: 10.10.0.0/24 through 10.39.0.0/24

## Provisioning with Ansible

After the infrastructure is deployed, you can provision the Active Directory environment using GOAD's Ansible playbooks:

1. **SSH to Ubuntu deployment box**:
   ```bash
   ssh ubuntu@<ubuntu-floating-ip>
   ```

2. **Clone GOAD repository** (if not already available)

3. **Run Ansible playbooks** from the GOAD repository:
   ```bash
   cd GOAD/ansible
   ansible-playbook -i inventory build.yml
   ```

Note: You may need to adapt the GOAD Ansible inventory files to match the IP addresses assigned by this OpenTofu deployment.

## Cost Optimization

### Disable Floating IPs
If you don't need external access to all VMs:
```hcl
enable_floating_ips = false
```

This saves floating IP quota and costs.

### Use Smaller Flavors
For testing or resource-constrained environments:
```hcl
dc_flavor_name     = "medium"      # 4GB RAM
server_flavor_name = "medium"      # 4GB RAM
linux_flavor_name  = "small.2gb"   # 2GB RAM
```

## Cleanup

To destroy all infrastructure:
```bash
tofu destroy
```

To destroy specific instances:
```bash
# Destroy and recreate with fewer instances
tofu apply -var="goad_instance_count=1"
```

## Security Warnings

This infrastructure is designed for **PENETRATION TESTING TRAINING** only:

- Security groups are **DISABLED** - all network traffic is allowed
- Windows VMs will have **vulnerable configurations** after GOAD provisioning
- **DO NOT** expose this infrastructure to the internet
- **DO NOT** use in production environments
- **DO NOT** store sensitive data on these systems

## Troubleshooting

### Authentication Issues
```bash
# Verify credentials are loaded
echo $OS_APPLICATION_CREDENTIAL_ID

# Re-source credentials
source ../app-cred-openrc.sh
```

### Resource Quota Issues
```bash
# Check your quotas
openstack quota show

# Check current usage
openstack limits show --absolute
```

### Image Not Found
```bash
# List available images
openstack image list | grep -i windows
openstack image list | grep -i ubuntu
openstack image list | grep -i kali
```

### Flavor Not Found
```bash
# List available flavors
openstack flavor list
```

## Network Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GOAD OpenStack Infrastructure             │
│                                                              │
│  Management Network (10.200.0.0/24)                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Ubuntu Deploy (10.200.0.250)  Kali (10.200.0.251) │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  GOAD Instance 1 (192.168.56.0/24)                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │ dc01 (.10)  dc02 (.11)  dc03 (.12)                │     │
│  │ srv02 (.22)  srv03 (.23)                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  GOAD Instance 2 (192.168.56.0/24) - Isolated Network       │
│  ┌────────────────────────────────────────────────────┐     │
│  │ dc01 (.10)  dc02 (.11)  dc03 (.12)                │     │
│  │ srv02 (.22)  srv03 (.23)                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ... (additional instances as configured)                    │
│  All use same IPs in isolated networks                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Additional Resources

- [GOAD GitHub Repository](https://github.com/Orange-Cyberdefense/GOAD)
- [GOAD Documentation](https://orange-cyberdefense.github.io/GOAD/)
- [OpenStack CLI Documentation](https://docs.openstack.org/python-openstackclient/)
- [OpenTofu Documentation](https://opentofu.org/docs/)
