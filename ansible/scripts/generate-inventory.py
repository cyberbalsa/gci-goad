#!/usr/bin/env python3
"""
Generate Ansible inventory from Terraform output
This creates an inventory file with all deployment boxes organized by network
"""

import json
import sys
import os
import subprocess

def get_terraform_output():
    """Get terraform output as JSON"""
    try:
        # Get the script's directory and find opentofu directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        opentofu_dir = os.path.join(project_root, 'opentofu')

        result = subprocess.run(
            ['tofu', 'output', '-json'],
            cwd=opentofu_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting terraform output: {e}", file=sys.stderr)
        sys.exit(1)

def generate_inventory(tf_output):
    """Generate inventory file content"""
    inventory = ["[deployment_boxes]"]

    # Get all ubuntu deployment box IPs
    ubuntu_ips = tf_output.get('ubuntu_deploy_floating_ips', {}).get('value', [])
    ubuntu_names = tf_output.get('ubuntu_deploy_names', {}).get('value', [])

    if ubuntu_ips:
        for idx, ip in enumerate(ubuntu_ips):
            if ip:  # Only add if IP exists
                name = ubuntu_names[idx] if idx < len(ubuntu_names) else f"goad-{idx+1}-ubuntu-deploy"
                inventory.append(f"{name} ansible_host={ip} ansible_user=cyberrange network_id={idx+1}")

    inventory.append("")
    inventory.append("[deployment_boxes:vars]")
    inventory.append("ansible_python_interpreter=/usr/bin/python3")
    inventory.append("ansible_ssh_common_args='-o StrictHostKeyChecking=no -J sshjump@ssh.cyberrange.rit.edu'")
    inventory.append("ansible_password=Cyberrange123!")

    # Add Kali boxes
    inventory.append("")
    inventory.append("# Kali Pentesting Boxes")
    inventory.append("[kali_boxes]")
    kali_ips = tf_output.get('kali_floating_ips', {}).get('value', [])
    kali_names = tf_output.get('kali_names', {}).get('value', [])
    for idx, ip in enumerate(kali_ips):
        if ip:
            name = kali_names[idx] if idx < len(kali_names) else f"goad-{idx+1}-kali"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    inventory.append("")
    inventory.append("[kali_boxes:vars]")
    inventory.append("ansible_python_interpreter=/usr/bin/python3")
    inventory.append("ansible_ssh_common_args='-o StrictHostKeyChecking=no -J sshjump@ssh.cyberrange.rit.edu'")
    inventory.append("ansible_user=cyberrange")
    inventory.append("ansible_password=Cyberrange123!")

    # Add Windows hosts
    inventory.append("")
    inventory.append("# Windows Domain Controllers")
    inventory.append("[windows_dc01]")
    dc01_ips = tf_output.get('dc01_floating_ips', {}).get('value', [])
    dc01_names = tf_output.get('dc01_names', {}).get('value', [])
    for idx, ip in enumerate(dc01_ips):
        if ip:
            name = dc01_names[idx] if idx < len(dc01_names) else f"goad-{idx+1}-dc01"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    inventory.append("")
    inventory.append("[windows_dc02]")
    dc02_ips = tf_output.get('dc02_floating_ips', {}).get('value', [])
    dc02_names = tf_output.get('dc02_names', {}).get('value', [])
    for idx, ip in enumerate(dc02_ips):
        if ip:
            name = dc02_names[idx] if idx < len(dc02_names) else f"goad-{idx+1}-dc02"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    inventory.append("")
    inventory.append("[windows_dc03]")
    dc03_ips = tf_output.get('dc03_floating_ips', {}).get('value', [])
    dc03_names = tf_output.get('dc03_names', {}).get('value', [])
    for idx, ip in enumerate(dc03_ips):
        if ip:
            name = dc03_names[idx] if idx < len(dc03_names) else f"goad-{idx+1}-dc03"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    inventory.append("")
    inventory.append("# Windows Servers")
    inventory.append("[windows_srv02]")
    srv02_ips = tf_output.get('srv02_floating_ips', {}).get('value', [])
    srv02_names = tf_output.get('srv02_names', {}).get('value', [])
    for idx, ip in enumerate(srv02_ips):
        if ip:
            name = srv02_names[idx] if idx < len(srv02_names) else f"goad-{idx+1}-srv02"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    inventory.append("")
    inventory.append("[windows_srv03]")
    srv03_ips = tf_output.get('srv03_floating_ips', {}).get('value', [])
    srv03_names = tf_output.get('srv03_names', {}).get('value', [])
    for idx, ip in enumerate(srv03_ips):
        if ip:
            name = srv03_names[idx] if idx < len(srv03_names) else f"goad-{idx+1}-srv03"
            inventory.append(f"{name} ansible_host={ip} network_id={idx+1}")

    # Windows group aggregations
    inventory.append("")
    inventory.append("[windows_domain_controllers:children]")
    inventory.append("windows_dc01")
    inventory.append("windows_dc02")
    inventory.append("windows_dc03")

    inventory.append("")
    inventory.append("[windows_servers:children]")
    inventory.append("windows_srv02")
    inventory.append("windows_srv03")

    inventory.append("")
    inventory.append("[windows:children]")
    inventory.append("windows_domain_controllers")
    inventory.append("windows_servers")

    # WinRM configuration for Windows hosts
    inventory.append("")
    inventory.append("[windows:vars]")
    inventory.append("ansible_user=cyberrange")
    inventory.append("ansible_password=Cyberrange123!")
    inventory.append("ansible_connection=winrm")
    inventory.append("ansible_winrm_transport=ntlm")
    inventory.append("ansible_winrm_server_cert_validation=ignore")
    inventory.append("ansible_port=5986")
    inventory.append("ansible_winrm_scheme=https")
    inventory.append("# WinRM over SOCKS5 proxy")
    inventory.append("ansible_winrm_proxy=socks5h://ssh.cyberrange.rit.edu:1080")
    inventory.append("# Disable become - WinRM doesn't support privilege escalation via sudo")
    inventory.append("become=false")

    # Add network information for orchestration
    inventory.append("")
    inventory.append("# Network information from Terraform")
    goad_instances = tf_output.get('deployment_summary', {}).get('value', {}).get('goad_instances', 0)
    inventory.append(f"# Total GOAD instances: {goad_instances}")
    inventory.append(f"# Total deployment boxes: {len(ubuntu_ips)}")
    inventory.append(f"# Total Kali boxes: {len(kali_ips)}")
    inventory.append(f"# Total Windows VMs: {len(dc01_ips) + len(dc02_ips) + len(dc03_ips) + len(srv02_ips) + len(srv03_ips)}")

    return "\n".join(inventory)

def main():
    """Main function"""
    print("Generating inventory from Terraform output...")
    tf_output = get_terraform_output()
    inventory = generate_inventory(tf_output)

    # Get the script's directory and find inventory file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inventory_file = os.path.join(os.path.dirname(script_dir), 'inventory', 'hosts')

    with open(inventory_file, 'w') as f:
        f.write(inventory)

    print(f"Inventory written to {inventory_file}")
    print("\nInventory preview:")
    print(inventory)

if __name__ == '__main__':
    main()
