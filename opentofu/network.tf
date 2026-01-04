# Network configuration for GOAD infrastructure
# Creates separate networks for each GOAD instance and a management network
# Security groups are DISABLED for network-based penetration testing

# External network data source
data "openstack_networking_network_v2" "ext_net" {
  name = var.external_network
}

# Management network for Ubuntu deployment box and Kali
resource "openstack_networking_network_v2" "mgmt_net" {
  name                  = "goad-mgmt-net"
  port_security_enabled = false  # Disable security groups for unrestricted network attacks
}

resource "openstack_networking_subnet_v2" "mgmt_subnet" {
  name            = "goad-mgmt-subnet"
  network_id      = openstack_networking_network_v2.mgmt_net.id
  cidr            = var.mgmt_subnet_cidr
  ip_version      = 4
  dns_nameservers = ["129.21.3.17", "129.21.4.18"]
}

# GOAD instance networks (one per GOAD copy)
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

# Single router for all networks
resource "openstack_networking_router_v2" "goad_router" {
  name                = "goad-router"
  external_network_id = data.openstack_networking_network_v2.ext_net.id
}

# Router interface for management network
resource "openstack_networking_router_interface_v2" "mgmt_router_interface" {
  router_id = openstack_networking_router_v2.goad_router.id
  subnet_id = openstack_networking_subnet_v2.mgmt_subnet.id
}

# Router interfaces for GOAD instance networks
resource "openstack_networking_router_interface_v2" "goad_router_interface" {
  count     = var.goad_instance_count
  router_id = openstack_networking_router_v2.goad_router.id
  subnet_id = openstack_networking_subnet_v2.goad_subnet[count.index].id
}
