# Instance configuration for GOAD infrastructure
# Deploys multiple GOAD instances (5 Windows VMs each) plus management boxes

# Data sources for images
data "openstack_images_image_v2" "windows_2019" {
  name        = var.windows_server_2019_image
  most_recent = true
}

data "openstack_images_image_v2" "windows_2016" {
  name        = var.windows_server_2016_image
  most_recent = true
}

data "openstack_images_image_v2" "ubuntu" {
  name        = var.ubuntu_image_name
  most_recent = true
}

data "openstack_images_image_v2" "kali" {
  name        = var.kali_image_name
  most_recent = true
}

# ============================================================================
# GOAD INSTANCES - Domain Controllers and Servers
# ============================================================================

# DC01 - Primary Domain Controller for sevenkingdoms.local (Windows Server 2019)
resource "openstack_compute_instance_v2" "dc01" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-dc01"
  flavor_name = var.dc_flavor_name
  key_pair    = var.keypair

  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.10"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.windows_2019.id
    source_type           = "image"
    volume_size           = var.windows_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# DC02 - Domain Controller for north.sevenkingdoms.local (Windows Server 2019)
resource "openstack_compute_instance_v2" "dc02" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-dc02"
  flavor_name = var.dc_flavor_name
  key_pair    = var.keypair

  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.11"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.windows_2019.id
    source_type           = "image"
    volume_size           = var.windows_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# DC03 - Domain Controller for essos.local (Windows Server 2016)
resource "openstack_compute_instance_v2" "dc03" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-dc03"
  flavor_name = var.dc_flavor_name
  key_pair    = var.keypair

  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.12"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.windows_2016.id
    source_type           = "image"
    volume_size           = var.windows_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# SRV02 - Member server in north.sevenkingdoms.local (Windows Server 2019)
resource "openstack_compute_instance_v2" "srv02" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-srv02"
  flavor_name = var.server_flavor_name
  key_pair    = var.keypair

  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.22"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.windows_2019.id
    source_type           = "image"
    volume_size           = var.windows_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# SRV03 - Member server in essos.local (Windows Server 2016)
resource "openstack_compute_instance_v2" "srv03" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-srv03"
  flavor_name = var.server_flavor_name
  key_pair    = var.keypair

  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.23"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.windows_2016.id
    source_type           = "image"
    volume_size           = var.windows_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# ============================================================================
# MANAGEMENT BOXES - Ubuntu Deployment Server and Kali Pentesting Box
# ============================================================================

# Ubuntu Deployment Box - One per GOAD network for Ansible provisioning
resource "openstack_compute_instance_v2" "ubuntu_deploy" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-ubuntu-deploy"
  flavor_name = var.deploy_flavor_name
  key_pair    = var.keypair
  user_data = file("${path.module}/debian-userdata.yaml")
  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.250"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.ubuntu.id
    source_type           = "image"
    volume_size           = var.linux_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# Kali Linux Box - One per GOAD network for penetration testing
resource "openstack_compute_instance_v2" "kali" {
  count       = var.goad_instance_count
  name        = "goad-${count.index + 1}-kali"
  flavor_name = var.kali_flavor_name
  key_pair    = var.keypair
  user_data = file("${path.module}/debian-userdata.yaml")
  network {
    uuid        = openstack_networking_network_v2.goad_net[count.index].id
    fixed_ip_v4 = "192.168.56.251"
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.kali.id
    source_type           = "image"
    volume_size           = var.linux_disk_size
    destination_type      = "volume"
    delete_on_termination = true
  }

  depends_on = [
    null_resource.network_ready_delay
  ]
}

# ============================================================================
# FLOATING IPs - For external access to instances
# ============================================================================

# Floating IPs for DC01 instances
resource "openstack_networking_floatingip_v2" "dc01_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IPs for DC02 instances
resource "openstack_networking_floatingip_v2" "dc02_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IPs for DC03 instances
resource "openstack_networking_floatingip_v2" "dc03_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IPs for SRV02 instances
resource "openstack_networking_floatingip_v2" "srv02_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IPs for SRV03 instances
resource "openstack_networking_floatingip_v2" "srv03_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IP for Ubuntu deployment boxes
resource "openstack_networking_floatingip_v2" "ubuntu_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# Floating IP for Kali boxes
resource "openstack_networking_floatingip_v2" "kali_fip" {
  count = var.enable_floating_ips ? var.goad_instance_count : 0
  pool  = var.external_network
}

# ============================================================================
# PORT DATA SOURCES - Get port IDs for floating IP associations
# ============================================================================

data "openstack_networking_port_v2" "dc01_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.dc01[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "dc02_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.dc02[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "dc03_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.dc03[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "srv02_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.srv02[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "srv03_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.srv03[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "ubuntu_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.ubuntu_deploy[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

data "openstack_networking_port_v2" "kali_port" {
  count      = var.enable_floating_ips ? var.goad_instance_count : 0
  device_id  = openstack_compute_instance_v2.kali[count.index].id
  network_id = openstack_networking_network_v2.goad_net[count.index].id
}

# ============================================================================
# FLOATING IP ASSOCIATIONS
# ============================================================================

resource "openstack_networking_floatingip_associate_v2" "dc01_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.dc01_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.dc01_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "dc02_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.dc02_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.dc02_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "dc03_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.dc03_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.dc03_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "srv02_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.srv02_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.srv02_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "srv03_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.srv03_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.srv03_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "ubuntu_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.ubuntu_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.ubuntu_port[count.index].id
}

resource "openstack_networking_floatingip_associate_v2" "kali_fip_assoc" {
  count       = var.enable_floating_ips ? var.goad_instance_count : 0
  floating_ip = openstack_networking_floatingip_v2.kali_fip[count.index].address
  port_id     = data.openstack_networking_port_v2.kali_port[count.index].id
}
