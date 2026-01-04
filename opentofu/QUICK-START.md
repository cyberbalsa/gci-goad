# GOAD OpenStack Quick Start

## One-Time Setup

```bash
# 1. Source OpenStack credentials
source ../app-cred-openrc.sh

# 2. Verify connectivity
openstack server list

# 3. Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# 4. Edit terraform.tfvars - REQUIRED CHANGES:
#    - Set keypair to your SSH key name
#    - Set goad_instance_count (default: 30)
nano terraform.tfvars
```

## Deploy Infrastructure

### Option 1: Using Deploy Script (Recommended)
```bash
./deploy.sh
```

### Option 2: Manual Deployment
```bash
# Initialize
tofu init

# Validate
tofu validate

# Plan
tofu plan

# Deploy
tofu apply
```

## Quick Commands

```bash
# Deploy with different instance count
tofu apply -var="goad_instance_count=10"

# Show deployment summary
tofu output deployment_summary

# Show all IPs
tofu output all_floating_ips

# Show SSH commands
tofu output ssh_commands

# Destroy everything
tofu destroy
```

## What Gets Deployed

### With goad_instance_count=30
- **150 Windows VMs** (30 GOAD instances × 5 VMs each)
  - 90 Domain Controllers (dc01, dc02, dc03 per instance)
  - 60 Member Servers (srv02, srv03 per instance)
- **2 Linux VMs**
  - 1 Ubuntu deployment box
  - 1 Kali Linux box
- **31 Networks** (30 GOAD + 1 management)
- **152 Floating IPs** (if enabled)

### Networks Created
- Management: 10.200.0.0/24
- Instance 1: 10.10.0.0/24
- Instance 2: 10.11.0.0/24
- ...
- Instance 30: 10.39.0.0/24

## Resource Requirements (30 instances)

| Resource | Required | Check Command |
|----------|----------|---------------|
| RAM | ~1 TB | `openstack quota show` |
| vCPUs | 300 | `openstack quota show` |
| Disk | 12 TB | `openstack quota show` |
| Floating IPs | 152 | `openstack floating ip list` |
| Networks | 31 | `openstack network list` |

## Post-Deployment

```bash
# 1. Get Ubuntu deployment box IP
tofu output ubuntu_deploy_floating_ip

# 2. SSH to Ubuntu box
ssh ubuntu@<ip-address>

# 3. Install Ansible and dependencies
sudo apt update
sudo apt install -y ansible python3-pip

# 4. Clone GOAD repository (if needed)
git clone https://github.com/Orange-Cyberdefense/GOAD.git

# 5. Configure and run GOAD Ansible playbooks
# (Follow GOAD documentation)
```

## Accessing VMs

```bash
# Get Kali IP
tofu output kali_floating_ip

# SSH to Kali
ssh kali@<kali-ip>

# RDP to Windows VMs (after provisioning)
# Use floating IPs from: tofu output dc01_floating_ips
```

## Common Issues

### Quota Exceeded
```bash
# Check quotas
openstack quota show

# Contact admin to increase quotas
```

### Keypair Not Found
```bash
# List keypairs
openstack keypair list

# Create keypair
openstack keypair create --public-key ~/.ssh/id_rsa.pub my-key

# Update terraform.tfvars
keypair = "my-key"
```

### Not Enough Floating IPs
```bash
# Check floating IP usage
openstack floating ip list

# Option 1: Disable floating IPs (deploy without external access)
enable_floating_ips = false

# Option 2: Request more quota
```

## Important Notes

Security groups are **DISABLED** (`port_security_enabled = false`) for:
- Network-based attacks (ARP poisoning, MITM, etc.)
- Responder/Inveigh
- SMB relay attacks

**Never expose this infrastructure to the internet!**

## Cleanup

```bash
# Destroy all infrastructure
tofu destroy

# Clean up state files
rm -f terraform.tfstate*
```

## Cost Optimization

### Deploy Fewer Instances
```bash
# Start with 1 instance for testing
tofu apply -var="goad_instance_count=1"

# Scale up as needed
tofu apply -var="goad_instance_count=30"
```

### Use Smaller Flavors
Edit terraform.tfvars:
```hcl
dc_flavor_name     = "medium"      # 4GB instead of 6GB
server_flavor_name = "medium"      # 4GB instead of 6GB
```

### Disable Floating IPs
```hcl
enable_floating_ips = false
```

## Files Reference

| File | Purpose |
|------|---------|
| `terraform.tfvars` | Your configuration (create from .example) |
| `variables.tf` | Variable definitions |
| `instances.tf` | VM definitions |
| `network.tf` | Network configuration |
| `outputs.tf` | Deployment outputs |
| `README.md` | Full documentation |
| `NETWORK-LAYOUT.md` | Network architecture details |
| `deploy.sh` | Automated deployment script |

## Next Steps

1. Deploy infrastructure
2. SSH to Ubuntu deployment box
3. Use GOAD Ansible playbooks to provision Active Directory
4. Attack from Kali box or Ubuntu box
5. Practice pentesting techniques

For detailed information, see README.md and NETWORK-LAYOUT.md
