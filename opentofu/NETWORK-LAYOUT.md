# GOAD OpenStack Network Layout

## Network Architecture

### Management Network
**CIDR**: 10.200.0.0/24
**Purpose**: Administrative access and deployment tools
**Port Security**: DISABLED

| Host | IP | Role | OS |
|------|-------|------|-----|
| goad-ubuntu-deploy | 10.200.0.250 | Ansible deployment server | Ubuntu 24.04 LTS |
| goad-kali | 10.200.0.251 | Penetration testing workstation | Kali Linux 2025 |

---

### GOAD Instance Networks

Each GOAD instance is isolated in its own network using the standard GOAD IP addressing scheme (192.168.56.0/24).

**All instances use the same IPs within their isolated networks:**

| Host | IP | Role | Domain |
|------|-------|------|--------|
| goad-N-dc01 | 192.168.56.10 | Primary Domain Controller | sevenkingdoms.local |
| goad-N-dc02 | 192.168.56.11 | Child Domain Controller | north.sevenkingdoms.local |
| goad-N-dc03 | 192.168.56.12 | Domain Controller | essos.local |
| goad-N-srv02 | 192.168.56.22 | Member Server (IIS, MSSQL) | north.sevenkingdoms.local |
| goad-N-srv03 | 192.168.56.23 | Member Server (MSSQL, ADCS) | essos.local |

**Note**: Since each instance is in a completely isolated OpenStack network, they can all use the same static IP addresses. This matches the standard GOAD configuration used in VirtualBox/VMware deployments.

---

## IP Allocation

All GOAD instances use the standard GOAD IP addressing scheme:

- **Network CIDR**: `192.168.56.0/24` (same for all instances, isolated by OpenStack network)
- **DC01**: `192.168.56.10`
- **DC02**: `192.168.56.11`
- **DC03**: `192.168.56.12`
- **SRV02**: `192.168.56.22`
- **SRV03**: `192.168.56.23`

### Examples for Multiple Instances

| Instance | Network Name | Network CIDR | All VM IPs |
|----------|-------------|--------------|------------|
| 1 | goad-instance-1-net | 192.168.56.0/24 | .10, .11, .12, .22, .23 |
| 2 | goad-instance-2-net | 192.168.56.0/24 | .10, .11, .12, .22, .23 |
| 3 | goad-instance-3-net | 192.168.56.0/24 | .10, .11, .12, .22, .23 |
| N | goad-instance-N-net | 192.168.56.0/24 | .10, .11, .12, .22, .23 |

---

## Routing

All networks are connected via a single OpenStack router (`goad-router`) with:
- External gateway: MAIN-NAT network
- Internal interfaces: All GOAD instance networks + management network

This allows:
- All instances to reach the internet
- All instances within the same network can communicate freely
- Cross-network communication between GOAD instances
- Management network can access all GOAD instances

---

## Security Configuration

**CRITICAL**: All networks have `port_security_enabled = false`

This means:
- ✓ No security group restrictions
- ✓ MAC address spoofing allowed
- ✓ IP address spoofing allowed
- ✓ ARP poisoning possible
- ✓ MITM attacks possible
- ✓ Full layer 2 attack capabilities

This configuration is **REQUIRED** for:
- Responder/Inveigh attacks
- LLMNR/NBT-NS poisoning
- SMB relay attacks
- IPv6 attacks
- MITM and network pivoting

**⚠ WARNING**: Never deploy this on production networks or expose to the internet!

---

## Floating IP Assignment

When `enable_floating_ips = true` (default), each instance receives a floating IP for external access:

- Ubuntu deployment box: 1 floating IP
- Kali box: 1 floating IP
- Each GOAD Windows VM: 1 floating IP per VM

**Total floating IPs needed** for N instances:
```
2 + (5 × N)
```

Examples:
- 1 instance: 7 floating IPs
- 10 instances: 52 floating IPs
- 30 instances: 152 floating IPs

Check your OpenStack quota before deployment:
```bash
openstack quota show
openstack floating ip list
```

---

## DNS Configuration

Each subnet is configured with RIT DNS servers:
- Primary DNS: 129.21.3.17
- Secondary DNS: 129.21.4.18

After GOAD Ansible provisioning, domain controllers will become the DNS servers for their respective domains.

---

## Network Access Scenarios

### Scenario 1: Pentesting from Kali
```
Kali (10.200.0.251)
  ↓ via router
GOAD Instance 1 Network (192.168.56.0/24)
  → Attack DC01 (192.168.56.10)
  → Attack SRV02 (192.168.56.22)
```

### Scenario 2: Cross-Instance Pivoting
```
Compromise GOAD-1-SRV02 (192.168.56.22)
  ↓ pivot via router
Lateral move to GOAD-2-DC01 (192.168.56.10)
  ↓ enumerate trust
Attack GOAD-2-DC03 (192.168.56.12)
```

**Note**: Both instances use the same IPs but are in separate isolated networks.

### Scenario 3: Deploying from Ubuntu
```
Ubuntu Deploy (10.200.0.250)
  ↓ Ansible over WinRM/SSH
All GOAD instances
  → Provision AD forests
  → Configure vulnerabilities
```

---

## Resource Requirements

### Per Instance (5 VMs)
- **RAM**: 30-40 GB (6 GB × 5 VMs)
- **vCPUs**: 10 (2 × 5 VMs)
- **Disk**: 400 GB (80 GB × 5 VMs)
- **Floating IPs**: 5 (if enabled)

### For 30 Instances (150 VMs)
- **RAM**: ~1 TB (960 GB for VMs + overhead)
- **vCPUs**: 300
- **Disk**: 12 TB
- **Floating IPs**: 150 (plus 2 for management boxes)
- **Networks**: 31 (30 GOAD + 1 management)
- **Subnets**: 31

---

## Network Troubleshooting

### Check connectivity from Kali to GOAD instance
```bash
# SSH to Kali
ssh kali@<kali-floating-ip>

# Ping GOAD-1-DC01
ping 192.168.56.10

# Check all GOAD-1 hosts
nmap -sn 192.168.56.0/24
```

### Check routing
```bash
# From any VM
ip route show
traceroute 10.200.0.250
```

### Verify port security is disabled
```bash
# From OpenStack CLI
openstack network show goad-instance-1-net | grep port_security
# Should show: port_security_enabled='False'
```

---

## Integration with GOAD Ansible

When running GOAD's Ansible playbooks, you'll need to create inventory files that match this network layout. Use the OpenTofu outputs to generate the inventory:

```bash
tofu output deployment_summary
```

This will show all IP addresses for creating your Ansible inventory files.
