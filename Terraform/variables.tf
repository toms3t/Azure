variable "resource_group_name" {
  description = "Resource group name"
}

variable "resource_group_location" {
  description = "Azure region"
}

variable "admin_username" {
  description = "VM username"
}

variable "admin_password" {
  description = "VM password"
}

variable "dns_label_prefix" {
  description = "DNS Name for the Public IP used to access the VM"
}

variable "ubuntu_os_version" {
  description = "The Ubuntu OS version"
}

variable "admin_sshkey" {
  type        = "string"
  description = "SSH key for authentication to the VM"
}
