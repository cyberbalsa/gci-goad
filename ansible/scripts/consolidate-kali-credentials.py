#!/usr/bin/env python3
"""
Consolidate Kali Credentials for Printout
Reads all Kali password files and creates a nicely formatted document
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def consolidate_credentials(creds_dir: str, output_file: str = None):
    """Read all Kali credential files and consolidate them"""

    creds_path = Path(creds_dir)

    if not creds_path.exists():
        print(f"Error: Credentials directory not found: {creds_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all password files
    password_files = sorted(creds_path.glob("*-password.txt"))

    if not password_files:
        print(f"Error: No password files found in {creds_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(password_files)} Kali credential files")

    # Default output file
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = creds_path.parent / f"KALI_CREDENTIALS_{timestamp}.txt"
    else:
        output_file = Path(output_file)

    # Read and consolidate credentials
    all_credentials = []

    for pwd_file in password_files:
        # Extract network/instance from filename
        # Format: goad-N-kali-password.txt
        filename = pwd_file.stem  # Remove .txt
        instance_name = filename.replace("-password", "")

        try:
            with open(pwd_file, 'r') as f:
                credentials = f.read().strip()

            # Parse credentials
            cred_lines = credentials.split('\n')
            cred_dict = {}
            for line in cred_lines:
                if ':' in line:
                    user, password = line.split(':', 1)
                    cred_dict[user] = password

            all_credentials.append({
                'instance': instance_name,
                'credentials': cred_dict
            })

        except Exception as e:
            print(f"Warning: Error reading {pwd_file}: {e}", file=sys.stderr)
            continue

    # Sort by instance name
    all_credentials.sort(key=lambda x: x['instance'])

    # Generate formatted output
    output_lines = []
    output_lines.append("="*80)
    output_lines.append("GOAD KALI LINUX CREDENTIALS")
    output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"Total Instances: {len(all_credentials)}")
    output_lines.append("="*80)
    output_lines.append("")
    output_lines.append("These credentials are for RDP and SSH access to Kali Linux boxes.")
    output_lines.append("Each Kali box has been configured with:")
    output_lines.append("  - pentester user (recommended for testing)")
    output_lines.append("  - xrdp enabled (RDP access on port 3389)")
    output_lines.append("  - All standard Kali tools pre-installed")
    output_lines.append("")
    output_lines.append("="*80)
    output_lines.append("")

    # Add credentials for each instance
    for idx, item in enumerate(all_credentials, 1):
        instance = item['instance']
        creds = item['credentials']

        output_lines.append(f"{idx}. {instance.upper()}")
        output_lines.append("-" * 80)

        # Display credentials in a table format
        for user in ['pentester', 'kali', 'cyberrange', 'root']:
            if user in creds:
                output_lines.append(f"  {user:15s} : {creds[user]}")

        output_lines.append("")

    output_lines.append("="*80)
    output_lines.append("USAGE NOTES")
    output_lines.append("="*80)
    output_lines.append("")
    output_lines.append("RDP Access:")
    output_lines.append("  Use any RDP client (Windows Remote Desktop, Remmina, etc.)")
    output_lines.append("  Connect to the Kali box floating IP address")
    output_lines.append("  Use 'pentester' user for best experience")
    output_lines.append("")
    output_lines.append("SSH Access:")
    output_lines.append("  ssh pentester@<floating-ip>")
    output_lines.append("  ssh -J sshjump@ssh.cyberrange.rit.edu pentester@<floating-ip>")
    output_lines.append("")
    output_lines.append("Security Notes:")
    output_lines.append("  - These are randomly generated passwords unique to each instance")
    output_lines.append("  - Keep this document secure")
    output_lines.append("  - Passwords are also stored on each Kali box at /home/pentester/password.txt")
    output_lines.append("")
    output_lines.append("="*80)

    # Write to output file
    output_content = "\n".join(output_lines)

    with open(output_file, 'w') as f:
        f.write(output_content)

    print(f"\n✓ Credentials consolidated to: {output_file}")
    print(f"  Total instances: {len(all_credentials)}")
    print(f"\nYou can print this file or share it with your team.")

    # Also print preview
    print("\n" + "="*80)
    print("PREVIEW (first 3 instances):")
    print("="*80)
    preview_lines = []
    for item in all_credentials[:3]:
        instance = item['instance']
        creds = item['credentials']
        preview_lines.append(f"\n{instance.upper()}:")
        if 'pentester' in creds:
            preview_lines.append(f"  pentester : {creds['pentester']}")
    print("\n".join(preview_lines))
    print("\n" + "="*80)

    return output_file


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Consolidate Kali credentials into a printable document',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--creds-dir',
        default='../credentials/kali',
        help='Path to directory containing Kali credential files (default: ../credentials/kali)'
    )

    parser.add_argument(
        '--output',
        help='Output file path (default: auto-generated in credentials directory)'
    )

    args = parser.parse_args()

    # Get the script's directory and resolve paths
    script_dir = Path(__file__).parent
    creds_dir = (script_dir / args.creds_dir).resolve()

    output_file = args.output
    if output_file:
        output_file = Path(output_file).resolve()

    consolidate_credentials(str(creds_dir), output_file)


if __name__ == '__main__':
    main()
