# GOAD Multi-Instance Deployment Project

## Overview

This project deploys multiple isolated GOAD (Game of Active Directory) lab instances on OpenStack infrastructure. Each instance is a complete, isolated Active Directory environment suitable for penetration testing training and practice.

**Key Features:**
- Multiple isolated GOAD instances (currently configured for 40)
- Each instance includes:
  - 5 Windows VMs (DC01, DC02, DC03, SRV02, SRV03)
  - 1 Ubuntu deployment box (pre-configured with GOAD)
  - 1 Kali Linux box (for pentesting)
- Parallel deployment using threading for efficient provisioning
- Terraform stub to bypass GOAD's native provisioning and use existing infrastructure

## Architecture

### Infrastructure Layers

```
┌─────────────────────────────────────────────────────────────┐
│ OpenStack Cloud                                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Instance 1 (Network 1)                                │  │
│  │  • 5 Windows VMs (isolated AD environment)           │  │
│  │  • 1 Ubuntu deploy box (GOAD pre-installed)          │  │
│  │  • 1 Kali box                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Instance 2 (Network 2)                                │  │
│  │  • Same structure, isolated network                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ... (38 more instances)                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Flow

```
OpenTofu → Infrastructure Provisioning
    ↓
Ansible → Deploy Box Preparation
    ↓
Threaded Python Script → Parallel GOAD Deployment
    ↓
40 Complete GOAD Labs Running Simultaneously
```

## Directory Structure

```
gci-goad/
├── opentofu/                  # Infrastructure as Code
│   ├── main.tf               # Main OpenTofu configuration
│   ├── instances.tf          # VM instance definitions
│   ├── network.tf            # Network configuration
│   ├── outputs.tf            # Output definitions
│   ├── variables.tf          # Variable definitions
│   └── terraform.tfvars      # Configuration values (40 instances)
│
├── ansible/                   # Configuration management
│   ├── ansible.cfg           # Ansible configuration
│   ├── inventory/
│   │   └── hosts             # Auto-generated from OpenTofu
│   ├── playbooks/
│   │   └── prepare-deployment-boxes.yml  # Prep Ubuntu boxes
│   ├── roles/
│   │   └── goad_deploy_box/  # Role to install GOAD prerequisites
│   │       ├── tasks/
│   │       │   └── main.yml
│   │       └── files/
│   │           └── terraform-stub.sh  # Fake terraform binary
│   └── scripts/
│       ├── generate-inventory.py      # Generate Ansible inventory
│       └── deploy-goad-threaded.py    # Parallel GOAD deployment
│
└── GOAD/                      # Git submodule (upstream GOAD)
```

## Deployment Process

### Stage 1: Infrastructure Provisioning (OpenTofu)

Deploy the base infrastructure on OpenStack:

```bash
cd opentofu
tofu init
tofu plan
tofu apply
```

This creates:
- 40 isolated networks (one per GOAD instance)
- 40 Ubuntu deployment boxes (one per network)
- 40 Kali boxes
- 200 Windows VMs (5 per instance × 40 instances)
- Floating IPs for external access to deployment boxes

**Key Configuration** (`terraform.tfvars`):
- `goad_instance_count = 40` - Number of complete GOAD labs
- Each instance is completely isolated in its own network
- All instances use the same internal IPs (192.168.56.x) since they're isolated

### Stage 2: Deployment Box Preparation (Ansible)

Prepare each Ubuntu deployment box with GOAD prerequisites:

```bash
cd ansible

# Generate inventory from OpenTofu outputs
python3 scripts/generate-inventory.py

# Prepare all deployment boxes
ansible-playbook playbooks/prepare-deployment-boxes.yml
```

This playbook:
1. Installs system packages (git, python3, sshpass, etc.)
2. Clones the GOAD repository to `/opt/goad`
3. **Creates a fake `terraform` binary** that always returns success
4. Sets up Python virtual environment with GOAD dependencies
5. Installs Ansible Galaxy collections for GOAD

**Why the Terraform Stub?**
- GOAD expects to provision infrastructure using Terraform/Proxmox
- We already have infrastructure from OpenTofu
- The stub (`/usr/local/bin/terraform`) tricks GOAD into thinking infrastructure is already provisioned
- GOAD then proceeds directly to Ansible configuration of the Windows VMs

### Stage 3: Parallel GOAD Deployment (Threaded Script)

Deploy GOAD across all 40 networks simultaneously:

```bash
cd ansible/scripts

# Deploy with default settings (10 parallel threads)
./deploy-goad-threaded.py

# Deploy with more parallelism (20 threads)
./deploy-goad-threaded.py --threads 20

# Deploy with different provider
./deploy-goad-threaded.py --provider proxmox
```

The script:
1. Reads the Ansible inventory to find all deployment boxes
2. For each box, SSHs in via jump host (`sshjump@ssh.cyberrange.rit.edu`) and runs: `python3 goad.py -p proxmox -l GOAD -m local`
3. Uses threading to run deployments in parallel
4. Monitors and reports progress in real-time
5. Provides a summary of successes/failures
6. Automatically retries failed deployments (configurable, default: 3 retries)
7. Logs all deployment output for debugging

**Deployment Timeline:**
- Sequential: ~40 instances × 30-60 minutes = 20-40 hours
- Parallel (10 threads): ~4 batches × 30-60 minutes = 2-4 hours
- Parallel (20 threads): ~2 batches × 30-60 minutes = 1-2 hours

## How the Terraform Stub Works

The stub (`ansible/roles/goad_deploy_box/files/terraform-stub.sh`) is installed as `/usr/local/bin/terraform` on each deployment box.

When GOAD runs terraform commands:
- `terraform version` → Returns fake version "Terraform v1.6.0"
- `terraform init` → Returns "Successfully initialized!"
- `terraform plan` → Returns "No changes needed"
- `terraform apply` → Returns "Apply complete! 0 resources"
- `terraform output` → Returns empty JSON `{}`

This allows GOAD to skip infrastructure provisioning and proceed directly to configuring the Windows VMs that OpenTofu already created.

## Configuration Files

### OpenTofu Configuration (`terraform.tfvars`)

```hcl
goad_instance_count = 40  # Number of complete GOAD labs

# Image names
windows_server_2019_image = "WindowsServer2019"
windows_server_2016_image = "WindowsServer2016"
ubuntu_image_name         = "ubuntu-noble-server"
kali_image_name           = "Kali2025"

# Flavors
dc_flavor_name     = "medium.6gb"  # 6GB RAM for DCs
server_flavor_name = "medium.6gb"  # 6GB RAM for servers
deploy_flavor_name = "medium"      # 4GB RAM for Ubuntu
kali_flavor_name   = "large"       # 8GB RAM for Kali

keypair = "homefedora"
enable_floating_ips = true
```

### Ansible Inventory (Auto-generated)

```ini
[deployment_boxes]
goad-1-ubuntu-deploy ansible_host=100.65.5.54 ansible_user=cyberrange network_id=1
goad-2-ubuntu-deploy ansible_host=100.65.5.92 ansible_user=cyberrange network_id=2
...
goad-40-ubuntu-deploy ansible_host=100.65.4.99 ansible_user=cyberrange network_id=40

[deployment_boxes:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no -J sshjump@ssh.cyberrange.rit.edu'
ansible_password=Cyberrange123!

# Total GOAD instances: 40
# Total deployment boxes: 40
```

**Note**: All connections route through SSH jump host `sshjump@ssh.cyberrange.rit.edu` for security.

## Resource Requirements

Per GOAD instance:
- 3 DCs × 6GB RAM = 18GB
- 2 Servers × 6GB RAM = 12GB
- 1 Ubuntu × 4GB RAM = 4GB
- 1 Kali × 8GB RAM = 8GB
- **Total per instance: 42GB RAM, 14 VCPUs**

For 40 instances:
- **Total RAM: 1,680GB (~1.6TB)**
- **Total VCPUs: 560**
- **Total VMs: 280**

## Network Topology

Each GOAD instance is in an isolated network:

```
Network 1 (192.168.56.0/24)
├── DC01:   192.168.56.10
├── DC02:   192.168.56.11
├── DC03:   192.168.56.12
├── SRV02:  192.168.56.22
├── SRV03:  192.168.56.23
├── Ubuntu: 192.168.56.250 (Floating IP: 100.65.5.54)
└── Kali:   192.168.56.251 (Floating IP: 100.65.5.X)

Network 2 (192.168.56.0/24) - Same IPs, different isolated network
├── DC01:   192.168.56.10
...

(All 40 networks use identical internal IPs due to isolation)
```

## Monitoring Deployment Progress

### Real-time Progress

The threaded deployment script shows progress:

```
[  1] Starting GOAD deployment on goad-1-ubuntu-deploy (100.65.5.54)
[  2] Starting GOAD deployment on goad-2-ubuntu-deploy (100.65.5.55)
...
[  1] ✓ GOAD deployment completed on goad-1-ubuntu-deploy (duration: 1847s)
[  5] ✗ GOAD deployment FAILED on goad-5-ubuntu-deploy (duration: 234s)
...
```

### Manual Monitoring

SSH into a deployment box to check progress:

```bash
ssh ubuntu@100.65.5.54
cd /opt/goad
source .venv/bin/activate

# Check GOAD status
python3 goad.py -p proxmox -l GOAD -m local --check

# View logs
tail -f ~/.goad/goad.log
```

## Troubleshooting

### Deployment Failures

If a GOAD deployment fails on a specific box:

```bash
# SSH into the failed deployment box
ssh ubuntu@<floating_ip>

# Activate GOAD environment
cd /opt/goad
source .venv/bin/activate

# Run GOAD manually with verbose output
python3 goad.py -p proxmox -l GOAD -m local -v

# Check Ansible logs
cd ~/.goad/
ls -la
```

### Terraform Stub Issues

Verify the stub is working:

```bash
ssh ubuntu@<floating_ip>
terraform version  # Should show "Terraform v1.6.0"
which terraform    # Should show "/usr/local/bin/terraform"
```

### Network Connectivity

Test connectivity from deployment box to Windows VMs:

```bash
ssh ubuntu@<floating_ip>
ping 192.168.56.10  # DC01
ping 192.168.56.11  # DC02
```

## Maintenance

### Updating GOAD

To update GOAD on all deployment boxes:

```bash
# Add task to ansible playbook
- name: Update GOAD repository
  git:
    repo: https://github.com/Orange-Cyberdefense/GOAD.git
    dest: /opt/goad
    version: main
    force: yes
  become: yes

# Run playbook
ansible-playbook playbooks/prepare-deployment-boxes.yml --tags update
```

### Re-running Failed Deployments

The deployment script can be run against a subset of hosts:

```bash
# Edit inventory to comment out successful deployments
# Then re-run
./deploy-goad-threaded.py
```

## Security Considerations

⚠️ **WARNING**: These GOAD environments are intentionally vulnerable!

- **DO NOT** expose these labs directly to the internet
- Floating IPs should be protected by firewall rules
- Only authorized users should have access
- These labs are for training/research only
- Regularly reset/rebuild labs to prevent abuse

## Performance Optimization

### Parallel Deployment Tuning

The optimal thread count depends on:
- Network bandwidth
- OpenStack API limits
- Ansible performance
- Your workstation's capacity

Start conservative (10 threads) and increase if stable:

```bash
# Test with 10 threads
./deploy-goad-threaded.py --threads 10

# Increase if no issues
./deploy-goad-threaded.py --threads 20
./deploy-goad-threaded.py --threads 30
```

### Resource Limits

Monitor OpenStack quotas:

```bash
source app-cred-openrc.sh
openstack quota show
openstack server list --all-projects | wc -l
```

## Future Enhancements

Potential improvements:
- [ ] Add health checks for deployed GOAD instances
- [ ] Implement automatic retry for failed deployments
- [ ] Create web dashboard for monitoring deployment status
- [ ] Add support for different GOAD lab types (GOAD-Light, MINILAB, SCCM)
- [ ] Implement automated testing of deployed labs
- [ ] Add cost tracking and reporting
- [ ] Create cleanup/teardown scripts

## References

- **GOAD Project**: https://github.com/Orange-Cyberdefense/GOAD
- **GOAD Documentation**: https://orange-cyberdefense.github.io/GOAD/
- **OpenTofu**: https://opentofu.org/
- **Ansible**: https://www.ansible.com/

## Project Timeline

1. ✅ OpenTofu infrastructure provisioning
2. ✅ Ansible playbook for deployment box preparation
3. ✅ Terraform stub implementation
4. ✅ Threaded deployment script
5. ⏳ Parallel GOAD deployment (in progress)
6. ⏳ Testing and validation

## Prerequisites

- **sshpass**: Required for password authentication in deployment script
  ```bash
  sudo dnf install sshpass  # Fedora/RHEL
  sudo apt install sshpass  # Debian/Ubuntu
  ```
- **SSH access**: Must have access to `sshjump@ssh.cyberrange.rit.edu`
- **Credentials**: Default password is `Cyberrange123!` for user `cyberrange`

## Support

For issues with:
- **Infrastructure**: Check OpenTofu state and OpenStack console
- **Deployment boxes**: Review Ansible playbook output
- **GOAD deployment**: Check GOAD logs on individual boxes
- **SSH connectivity**: Verify jump host access and credentials
- **This project**: See ansible/scripts/ for helper scripts

---

**Last Updated**: 2026-01-04
**Project Status**: Active Development
**Current Instance Count**: 40 GOAD labs
