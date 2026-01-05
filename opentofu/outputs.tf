# Outputs for GOAD infrastructure deployment
# Provides IP addresses and instance information for Ansible provisioning

# ============================================================================
# GOAD INSTANCE OUTPUTS
# ============================================================================

# DC01 outputs
output "dc01_floating_ips" {
  description = "Floating IPs for all DC01 instances"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.dc01_fip : fip.address] : []
}

output "dc01_internal_ips" {
  description = "Internal IPs for all DC01 instances"
  value       = [for vm in openstack_compute_instance_v2.dc01 : vm.access_ip_v4]
}

output "dc01_names" {
  description = "Names of all DC01 instances"
  value       = [for vm in openstack_compute_instance_v2.dc01 : vm.name]
}

# DC02 outputs
output "dc02_floating_ips" {
  description = "Floating IPs for all DC02 instances"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.dc02_fip : fip.address] : []
}

output "dc02_internal_ips" {
  description = "Internal IPs for all DC02 instances"
  value       = [for vm in openstack_compute_instance_v2.dc02 : vm.access_ip_v4]
}

output "dc02_names" {
  description = "Names of all DC02 instances"
  value       = [for vm in openstack_compute_instance_v2.dc02 : vm.name]
}

# DC03 outputs
output "dc03_floating_ips" {
  description = "Floating IPs for all DC03 instances"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.dc03_fip : fip.address] : []
}

output "dc03_internal_ips" {
  description = "Internal IPs for all DC03 instances"
  value       = [for vm in openstack_compute_instance_v2.dc03 : vm.access_ip_v4]
}

output "dc03_names" {
  description = "Names of all DC03 instances"
  value       = [for vm in openstack_compute_instance_v2.dc03 : vm.name]
}

# SRV02 outputs
output "srv02_floating_ips" {
  description = "Floating IPs for all SRV02 instances"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.srv02_fip : fip.address] : []
}

output "srv02_internal_ips" {
  description = "Internal IPs for all SRV02 instances"
  value       = [for vm in openstack_compute_instance_v2.srv02 : vm.access_ip_v4]
}

output "srv02_names" {
  description = "Names of all SRV02 instances"
  value       = [for vm in openstack_compute_instance_v2.srv02 : vm.name]
}

# SRV03 outputs
output "srv03_floating_ips" {
  description = "Floating IPs for all SRV03 instances"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.srv03_fip : fip.address] : []
}

output "srv03_internal_ips" {
  description = "Internal IPs for all SRV03 instances"
  value       = [for vm in openstack_compute_instance_v2.srv03 : vm.access_ip_v4]
}

output "srv03_names" {
  description = "Names of all SRV03 instances"
  value       = [for vm in openstack_compute_instance_v2.srv03 : vm.name]
}

# ============================================================================
# MANAGEMENT BOX OUTPUTS
# ============================================================================

# Ubuntu deployment box outputs
output "ubuntu_deploy_floating_ips" {
  description = "Floating IPs for all Ubuntu deployment boxes"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.ubuntu_fip : fip.address] : []
}

output "ubuntu_deploy_internal_ips" {
  description = "Internal IPs for all Ubuntu deployment boxes"
  value       = [for vm in openstack_compute_instance_v2.ubuntu_deploy : vm.access_ip_v4]
}

output "ubuntu_deploy_names" {
  description = "Names of all Ubuntu deployment boxes"
  value       = [for vm in openstack_compute_instance_v2.ubuntu_deploy : vm.name]
}

# Kali box outputs
output "kali_floating_ips" {
  description = "Floating IPs for all Kali boxes"
  value       = var.enable_floating_ips ? [for fip in openstack_networking_floatingip_v2.kali_fip : fip.address] : []
}

output "kali_internal_ips" {
  description = "Internal IPs for all Kali boxes"
  value       = [for vm in openstack_compute_instance_v2.kali : vm.access_ip_v4]
}

output "kali_names" {
  description = "Names of all Kali boxes"
  value       = [for vm in openstack_compute_instance_v2.kali : vm.name]
}

# ============================================================================
# NETWORK OUTPUTS
# ============================================================================

output "goad_network_ids" {
  description = "IDs of all GOAD instance networks"
  value       = [for net in openstack_networking_network_v2.goad_net : net.id]
}

output "goad_subnet_cidrs" {
  description = "CIDR blocks for all GOAD instance subnets"
  value       = [for subnet in openstack_networking_subnet_v2.goad_subnet : subnet.cidr]
}

# ============================================================================
# SUMMARY OUTPUT - Useful for Ansible inventory generation
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed GOAD infrastructure"
  value = {
    goad_instances       = var.goad_instance_count
    total_windows_vms    = var.goad_instance_count * 5
    total_ubuntu_boxes   = var.goad_instance_count
    total_kali_boxes     = var.goad_instance_count
    total_vms            = var.goad_instance_count * 7  # 5 Windows + 1 Ubuntu + 1 Kali per instance

    goad_instances_detail = [
      for i in range(var.goad_instance_count) : {
        instance_number = i + 1
        network_cidr    = "192.168.56.0/24"
        dc01_ip         = "192.168.56.10"
        dc02_ip         = "192.168.56.11"
        dc03_ip         = "192.168.56.12"
        srv02_ip        = "192.168.56.22"
        srv03_ip        = "192.168.56.23"
        ubuntu_ip       = "192.168.56.250"
        kali_ip         = "192.168.56.251"
        note            = "Isolated network - same IPs across all instances"
      }
    ]
  }
}

# ============================================================================
# QUICK ACCESS OUTPUTS
# ============================================================================

output "all_floating_ips" {
  description = "All floating IPs in the deployment"
  value = var.enable_floating_ips ? concat(
    [for fip in openstack_networking_floatingip_v2.dc01_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.dc02_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.dc03_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.srv02_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.srv03_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.ubuntu_fip : fip.address],
    [for fip in openstack_networking_floatingip_v2.kali_fip : fip.address]
  ) : []
}

output "ssh_commands" {
  description = "SSH commands to connect to Linux boxes"
  value = var.enable_floating_ips ? {
    ubuntu_boxes = [
      for i, fip in openstack_networking_floatingip_v2.ubuntu_fip :
      "ssh -i ~/.ssh/homefedora ubuntu@${fip.address}  # goad-${i + 1}-ubuntu-deploy"
    ]
    kali_boxes = [
      for i, fip in openstack_networking_floatingip_v2.kali_fip :
      "ssh -i ~/.ssh/homefedora kali@${fip.address}  # goad-${i + 1}-kali"
    ]
  } : {}
}
