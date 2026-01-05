# Network configuration for GOAD infrastructure
# Creates separate isolated networks for each GOAD instance
# Each network contains: 5 Windows VMs + 1 Ubuntu deployment box + 1 Kali box
# Security groups are DISABLED for network-based penetration testing

# External network data source
data "openstack_networking_network_v2" "ext_net" {
  name = var.external_network
}

# GOAD instance networks (one per GOAD instance)
resource "openstack_networking_network_v2" "goad_net" {
  count                 = var.goad_instance_count
  name                  = "goad-instance-${count.index + 1}-net"
  port_security_enabled = false  # Disable security groups for unrestricted network attacks
}

resource "openstack_networking_subnet_v2" "goad_subnet" {
  count           = var.goad_instance_count
  name            = "goad-instance-${count.index + 1}-subnet"
  network_id      = openstack_networking_network_v2.goad_net[count.index].id
  cidr            = "192.168.56.0/24"
  ip_version      = 4
  dns_nameservers = ["129.21.3.17", "129.21.4.18"]

  allocation_pool {
    start = "192.168.56.2"
    end   = "192.168.56.254"
  }
}

# Routers for each GOAD instance network
resource "openstack_networking_router_v2" "goad_router" {
  count               = var.goad_instance_count
  name                = "goad-instance-${count.index + 1}-router"
  external_network_id = data.openstack_networking_network_v2.ext_net.id
}

# Router interfaces for GOAD instance networks
resource "openstack_networking_router_interface_v2" "goad_router_interface" {
  count     = var.goad_instance_count
  router_id = openstack_networking_router_v2.goad_router[count.index].id
  subnet_id = openstack_networking_subnet_v2.goad_subnet[count.index].id
}

# Wait for networks to be fully ready before creating VMs
# OpenStack can report networks as up before they're actually ready to boot instances
resource "null_resource" "network_ready_delay" {
  count = var.goad_instance_count

  depends_on = [
    openstack_networking_subnet_v2.goad_subnet,
    openstack_networking_router_interface_v2.goad_router_interface
  ]

  provisioner "local-exec" {
    command = "sleep 5"
  }
}
