# OpenTofu variables for OpenStack GOAD deployment
# Note: OpenStack credentials are loaded from environment variables via app-cred-openrc.sh

# Number of GOAD instances to deploy
variable "goad_instance_count" {
  type        = number
  default     = 1
  description = "Number of complete GOAD lab instances to deploy (each has 5 Windows VMs + 1 Ubuntu + 1 Kali)"
}

# Network configuration
variable "external_network" {
  type    = string
  default = "MAIN-NAT"
}

# Image configuration
variable "windows_server_2019_image" {
  type    = string
  default = "WindowsServer2019"
  description = "Windows Server 2019 image for DC01, DC02, SRV02"
}

variable "windows_server_2016_image" {
  type    = string
  default = "WindowsServer2016"
  description = "Windows Server 2016 image for DC03, SRV03"
}

variable "ubuntu_image_name" {
  type    = string
  default = "ubuntu-noble-server"
}

variable "kali_image_name" {
  type    = string
  default = "Kali2025"
}

# Flavor configuration
variable "dc_flavor_name" {
  type        = string
  default     = "medium.6gb"
  description = "Flavor for domain controllers (6GB RAM, 2 VCPUs recommended)"
}

variable "server_flavor_name" {
  type        = string
  default     = "medium.6gb"
  description = "Flavor for member servers (6GB RAM, 2 VCPUs recommended)"
}

variable "deploy_flavor_name" {
  type        = string
  default     = "medium"
  description = "Flavor for Ubuntu deployment boxes (4GB RAM, 2 VCPUs)"
}

variable "kali_flavor_name" {
  type        = string
  default     = "large"
  description = "Flavor for Kali boxes (8GB RAM, 4 VCPUs)"
}

# SSH keypair (must be created in OpenStack first)
variable "keypair" {
  type        = string
  description = "Name of the SSH keypair to use for instance access"
}

# Floating IP configuration
variable "enable_floating_ips" {
  type        = bool
  default     = true
  description = "Whether to assign floating IPs to instances for external access"
}

# Windows VM disk size
variable "windows_disk_size" {
  type    = number
  default = 80
}

# Linux VM disk size
variable "linux_disk_size" {
  type    = number
  default = 50
}
