#!/usr/bin/env python3
"""
Threaded GOAD Deployment Script
Deploys GOAD across all networks simultaneously using threading

This script:
1. Reads the Ansible inventory to get all deployment boxes
2. Runs Ansible playbook to prepare all deployment boxes with GOAD prerequisites
3. For each deployment box, initiates GOAD provisioning via SSH
4. Uses threading to run all deployments in parallel
5. Monitors progress and reports status with comprehensive logging
"""

import subprocess
import threading
import sys
import time
import re
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import argparse
import logging


class DeploymentBox:
    """Represents a single GOAD deployment box"""

    def __init__(self, name: str, host: str, network_id: int):
        self.name = name
        self.host = host
        self.network_id = network_id
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.output = []
        self.error_output = []
        self.attempts = 0
        self.log_file = None

    def __repr__(self):
        return f"DeploymentBox({self.name}, {self.host}, network_{self.network_id})"


class GOADDeployer:
    """Manages threaded GOAD deployment across multiple networks"""

    def __init__(self, inventory_file: str, max_threads: int = 10, goad_provider: str = "proxmox",
                 max_retries: int = 3, log_dir: str = "./logs"):
        self.inventory_file = inventory_file
        self.max_threads = max_threads
        self.goad_provider = goad_provider
        self.max_retries = max_retries
        self.log_dir = Path(log_dir)
        self.deployment_boxes: List[DeploymentBox] = []
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(max_threads)

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up main logger
        self.setup_logging()

    def setup_logging(self):
        """Set up logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f"goad_deployment_{timestamp}.log"

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging to {log_file}")

    def parse_inventory(self) -> List[DeploymentBox]:
        """Parse Ansible inventory to extract deployment box information"""
        boxes = []

        try:
            with open(self.inventory_file, 'r') as f:
                lines = f.readlines()

            in_deployment_boxes = False
            for line in lines:
                line = line.strip()

                if line.startswith('[deployment_boxes]'):
                    in_deployment_boxes = True
                    continue

                if in_deployment_boxes:
                    # Stop if we hit another section or vars
                    if line.startswith('[') or not line or line.startswith('#'):
                        if line.startswith('[deployment_boxes:vars]'):
                            break
                        continue

                    # Parse line: name ansible_host=IP ansible_user=ubuntu network_id=N
                    match = re.match(r'(\S+)\s+ansible_host=(\S+).*network_id=(\d+)', line)
                    if match:
                        name, host, network_id = match.groups()
                        boxes.append(DeploymentBox(name, host, int(network_id)))

            print(f"Found {len(boxes)} deployment boxes in inventory")
            return boxes

        except FileNotFoundError:
            print(f"Error: Inventory file not found: {self.inventory_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing inventory: {e}", file=sys.stderr)
            sys.exit(1)

    def activate_windows_hosts(self):
        """Run Ansible playbook to activate Windows hosts before GOAD deployment"""
        print(f"\n{'='*80}")
        print("Activating Windows hosts...")
        print(f"{'='*80}\n")

        self.logger.info("Starting Ansible playbook to activate Windows hosts")

        # Determine the ansible directory (parent of scripts directory)
        script_dir = Path(__file__).parent
        ansible_dir = script_dir.parent
        playbook_path = "playbooks/activate-windows-hosts.yml"  # Relative to ansible dir

        # Build ansible-playbook command
        ansible_cmd = [
            'ansible-playbook',
            '-i', 'inventory/hosts',
            playbook_path
        ]

        # Create log file for Windows activation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        activation_log_file = self.log_dir.absolute() / f"windows_activation_{timestamp}.log"

        try:
            print(f"Running from: {ansible_dir}")
            print(f"Command: {' '.join(ansible_cmd)}")
            print(f"Logs: {activation_log_file}\n")

            # Run ansible-playbook from the ansible directory
            with open(activation_log_file, 'w') as log_f:
                result = subprocess.run(
                    ansible_cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(ansible_dir),
                    timeout=3600  # 60 minute timeout (40 instances * 5 VMs = 200 VMs might take a while)
                )

            if result.returncode == 0:
                msg = "✓ Windows activation completed successfully"
                print(msg)
                self.logger.info(msg)
                print(f"\n{'='*80}\n")
                return True
            else:
                msg = f"⚠ Windows activation had issues (return code {result.returncode}), but continuing..."
                print(msg)
                self.logger.warning(msg)
                print(f"Check log file for details: {activation_log_file}")

                # Print last 20 lines of log for immediate feedback
                try:
                    with open(activation_log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print("\nLast 20 lines of activation output:")
                            print("".join(lines[-20:]))
                except Exception:
                    pass

                print(f"\n{'='*80}\n")
                return True  # Continue anyway - activation issues shouldn't block GOAD deployment

        except subprocess.TimeoutExpired:
            msg = "⏱ Windows activation timed out after 60 minutes, but continuing..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

        except FileNotFoundError:
            msg = f"⚠ Windows activation playbook not found: {playbook_path}, skipping activation..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

        except Exception as e:
            msg = f"⚠ Error running Windows activation: {e}, but continuing..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

    def prepare_kali_boxes(self):
        """Run Ansible playbook to prepare Kali boxes"""
        print(f"\n{'='*80}")
        print("Preparing Kali pentesting boxes...")
        print(f"{'='*80}\n")

        self.logger.info("Starting Ansible playbook to prepare Kali boxes")

        # Determine the ansible directory (parent of scripts directory)
        script_dir = Path(__file__).parent
        ansible_dir = script_dir.parent
        playbook_path = "playbooks/prepare-kali-boxes.yml"  # Relative to ansible dir

        # Build ansible-playbook command
        ansible_cmd = [
            'ansible-playbook',
            '-i', 'inventory/hosts',
            playbook_path
        ]

        # Create log file for Kali preparation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        kali_log_file = self.log_dir.absolute() / f"kali_preparation_{timestamp}.log"

        try:
            print(f"Running from: {ansible_dir}")
            print(f"Command: {' '.join(ansible_cmd)}")
            print(f"Logs: {kali_log_file}\n")

            # Run ansible-playbook from the ansible directory
            with open(kali_log_file, 'w') as log_f:
                result = subprocess.run(
                    ansible_cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(ansible_dir),
                    timeout=1800  # 30 minute timeout
                )

            if result.returncode == 0:
                msg = "✓ Kali preparation completed successfully"
                print(msg)
                self.logger.info(msg)

                # Display credentials location
                creds_dir = ansible_dir / "credentials" / "kali"
                if creds_dir.exists():
                    print(f"\nKali credentials saved to: {creds_dir}")
                    print("Use these for RDP access to Kali boxes")

                print(f"\n{'='*80}\n")
                return True
            else:
                msg = f"⚠ Kali preparation had issues (return code {result.returncode}), but continuing..."
                print(msg)
                self.logger.warning(msg)
                print(f"Check log file for details: {kali_log_file}")

                # Print last 20 lines of log for immediate feedback
                try:
                    with open(kali_log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print("\nLast 20 lines of Kali preparation output:")
                            print("".join(lines[-20:]))
                except Exception:
                    pass

                print(f"\n{'='*80}\n")
                return True  # Continue anyway

        except subprocess.TimeoutExpired:
            msg = "⏱ Kali preparation timed out after 30 minutes, but continuing..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

        except FileNotFoundError:
            msg = f"⚠ Kali preparation playbook not found: {playbook_path}, skipping..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

        except Exception as e:
            msg = f"⚠ Error running Kali preparation: {e}, but continuing..."
            print(msg)
            self.logger.warning(msg)
            print(f"\n{'='*80}\n")
            return True  # Continue anyway

    def prepare_deployment_boxes(self):
        """Run Ansible playbook to prepare all deployment boxes"""
        print(f"\n{'='*80}")
        print("Preparing deployment boxes with Ansible...")
        print(f"{'='*80}\n")

        self.logger.info("Starting Ansible playbook to prepare deployment boxes")

        # Determine the ansible directory (parent of scripts directory)
        script_dir = Path(__file__).parent
        ansible_dir = script_dir.parent
        playbook_path = "playbooks/prepare-deployment-boxes.yml"  # Relative to ansible dir

        # Build ansible-playbook command - use relative paths since we'll cd to ansible dir
        ansible_cmd = [
            'ansible-playbook',
            '-i', 'inventory/hosts',
            playbook_path
        ]

        # Create log file for Ansible preparation (use absolute path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prep_log_file = self.log_dir.absolute() / f"ansible_preparation_{timestamp}.log"

        try:
            print(f"Running from: {ansible_dir}")
            print(f"Command: {' '.join(ansible_cmd)}")
            print(f"Logs: {prep_log_file}\n")

            # Run ansible-playbook from the ansible directory so it picks up ansible.cfg
            with open(prep_log_file, 'w') as log_f:
                result = subprocess.run(
                    ansible_cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(ansible_dir),  # Run from ansible directory
                    timeout=1800  # 30 minute timeout
                )

            if result.returncode == 0:
                msg = "✓ Ansible preparation completed successfully"
                print(msg)
                self.logger.info(msg)
                print(f"\n{'='*80}\n")
                return True
            else:
                msg = f"✗ Ansible preparation failed with return code {result.returncode}"
                print(msg)
                self.logger.error(msg)
                print(f"Check log file for details: {prep_log_file}")

                # Print last 20 lines of log for immediate feedback
                try:
                    with open(prep_log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print("\nLast 20 lines of Ansible output:")
                            print("".join(lines[-20:]))
                except Exception:
                    pass

                sys.exit(1)

        except subprocess.TimeoutExpired:
            msg = "⏱ Ansible preparation timed out after 30 minutes"
            print(msg)
            self.logger.error(msg)
            sys.exit(1)

        except FileNotFoundError:
            msg = f"✗ Ansible playbook not found: {playbook_path}"
            print(msg)
            self.logger.error(msg)
            sys.exit(1)

        except Exception as e:
            msg = f"✗ Error running Ansible preparation: {e}"
            print(msg)
            self.logger.error(msg)
            sys.exit(1)

    def deploy_goad_on_box(self, box: DeploymentBox):
        """Deploy GOAD on a single deployment box with retry logic"""
        self.semaphore.acquire()

        try:
            # Create log file for this deployment
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            box.log_file = self.log_dir / f"deploy_{box.name}_{timestamp}.log"

            success = False
            attempt = 0

            while attempt < self.max_retries and not success:
                attempt += 1
                box.attempts = attempt

                with self.lock:
                    box.status = "running"
                    if box.start_time is None:
                        box.start_time = datetime.now()

                    msg = f"[{box.network_id:3d}] Starting GOAD deployment on {box.name} ({box.host}) - Attempt {attempt}/{self.max_retries}"
                    print(msg)
                    self.logger.info(msg)

                # SSH command to run GOAD provisioning
                # Use sshpass for password authentication and jump host to reach deployment boxes
                # Note: The remote command must be a single string argument to SSH
                remote_cmd = f'cd /opt/goad && source .venv/bin/activate && python3 goad.py -p {self.goad_provider} -l GOAD -m local'

                ssh_cmd = [
                    'sshpass', '-p', 'Cyberrange123!',
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'LogLevel=ERROR',
                    '-J', 'sshjump@ssh.cyberrange.rit.edu',
                    f'cyberrange@{box.host}',
                    remote_cmd
                ]

                try:
                    # Run the SSH command
                    result = subprocess.run(
                        ssh_cmd,
                        capture_output=True,
                        text=True,
                        timeout=7200  # 2 hour timeout
                    )

                    # Save output to log file
                    with open(box.log_file, 'a') as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"Attempt {attempt}/{self.max_retries} - {datetime.now()}\n")
                        f.write(f"{'='*80}\n")
                        f.write(f"Command: {' '.join(ssh_cmd)}\n")
                        f.write(f"Return code: {result.returncode}\n")
                        f.write(f"\n--- STDOUT ---\n")
                        f.write(result.stdout)
                        f.write(f"\n--- STDERR ---\n")
                        f.write(result.stderr)
                        f.write(f"\n{'='*80}\n")

                    with self.lock:
                        box.end_time = datetime.now()
                        duration = (box.end_time - box.start_time).total_seconds()

                        if result.returncode == 0:
                            box.status = "success"
                            success = True
                            msg = f"[{box.network_id:3d}] ✓ GOAD deployment completed on {box.name} (duration: {duration:.0f}s, attempts: {attempt})"
                            print(msg)
                            self.logger.info(msg)
                        else:
                            box.error_output = result.stderr.split('\n')

                            if attempt < self.max_retries:
                                msg = f"[{box.network_id:3d}] ⚠ GOAD deployment failed on {box.name}, retrying ({attempt}/{self.max_retries})"
                                print(msg)
                                self.logger.warning(msg)
                                self.logger.warning(f"[{box.network_id:3d}] Error preview: {result.stderr[:200]}")
                                # Wait a bit before retry to let any race conditions settle
                                time.sleep(10)
                            else:
                                box.status = "failed"
                                msg = f"[{box.network_id:3d}] ✗ GOAD deployment FAILED on {box.name} after {attempt} attempts (duration: {duration:.0f}s)"
                                print(msg)
                                self.logger.error(msg)
                                self.logger.error(f"[{box.network_id:3d}] Error: {result.stderr[:200]}")

                        box.output = result.stdout.split('\n')

                except subprocess.TimeoutExpired as e:
                    with self.lock:
                        # Save timeout info to log
                        with open(box.log_file, 'a') as f:
                            f.write(f"\n{'='*80}\n")
                            f.write(f"Attempt {attempt}/{self.max_retries} - TIMEOUT - {datetime.now()}\n")
                            f.write(f"{'='*80}\n")

                        if attempt < self.max_retries:
                            msg = f"[{box.network_id:3d}] ⏱ GOAD deployment TIMEOUT on {box.name}, retrying ({attempt}/{self.max_retries})"
                            print(msg)
                            self.logger.warning(msg)
                            time.sleep(10)
                        else:
                            box.status = "timeout"
                            box.end_time = datetime.now()
                            msg = f"[{box.network_id:3d}] ⏱ GOAD deployment TIMEOUT on {box.name} after {attempt} attempts"
                            print(msg)
                            self.logger.error(msg)

        except Exception as e:
            with self.lock:
                box.status = "error"
                box.end_time = datetime.now()
                msg = f"[{box.network_id:3d}] ✗ Error deploying GOAD on {box.name}: {e}"
                print(msg)
                self.logger.error(msg)

                # Save error to log file
                if box.log_file:
                    with open(box.log_file, 'a') as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"EXCEPTION - {datetime.now()}\n")
                        f.write(f"{'='*80}\n")
                        f.write(str(e))
                        f.write(f"\n{'='*80}\n")

        finally:
            self.semaphore.release()

    def deploy_all(self):
        """Deploy GOAD on all boxes using threading"""
        self.deployment_boxes = self.parse_inventory()

        if not self.deployment_boxes:
            print("No deployment boxes found in inventory!")
            return

        # Activate Windows hosts before GOAD deployment
        self.activate_windows_hosts()

        # Prepare Kali boxes with pentester user and RDP access
        self.prepare_kali_boxes()

        # Prepare all deployment boxes with Ansible before starting GOAD deployment
        self.prepare_deployment_boxes()

        print(f"\n{'='*80}")
        print(f"Starting threaded GOAD deployment")
        print(f"Total instances: {len(self.deployment_boxes)}")
        print(f"Max parallel threads: {self.max_threads}")
        print(f"GOAD provider: {self.goad_provider}")
        print(f"{'='*80}\n")

        start_time = datetime.now()

        # Create and start threads
        threads = []
        for box in self.deployment_boxes:
            thread = threading.Thread(target=self.deploy_goad_on_box, args=(box,))
            thread.start()
            threads.append(thread)
            time.sleep(0.1)  # Small delay to stagger starts

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Print summary
        self.print_summary(total_duration)

    def print_summary(self, total_duration: float):
        """Print deployment summary"""
        success_count = sum(1 for box in self.deployment_boxes if box.status == "success")
        failed_count = sum(1 for box in self.deployment_boxes if box.status == "failed")
        timeout_count = sum(1 for box in self.deployment_boxes if box.status == "timeout")
        error_count = sum(1 for box in self.deployment_boxes if box.status == "error")

        # Count retries
        total_attempts = sum(box.attempts for box in self.deployment_boxes)
        retried_count = sum(1 for box in self.deployment_boxes if box.attempts > 1)

        print(f"\n{'='*80}")
        print(f"GOAD Deployment Summary")
        print(f"{'='*80}")
        print(f"Total instances:     {len(self.deployment_boxes)}")
        print(f"Successful:          {success_count} ✓")
        print(f"Failed:              {failed_count} ✗")
        print(f"Timeout:             {timeout_count} ⏱")
        print(f"Error:               {error_count} ✗")
        print(f"Total attempts:      {total_attempts}")
        print(f"Retried instances:   {retried_count}")
        print(f"Total duration:      {total_duration:.0f}s ({total_duration/60:.1f} minutes)")
        print(f"Logs directory:      {self.log_dir}")
        print(f"{'='*80}\n")

        if failed_count > 0 or timeout_count > 0 or error_count > 0:
            print("Failed/Timeout/Error deployments:")
            for box in self.deployment_boxes:
                if box.status in ["failed", "timeout", "error"]:
                    duration = (box.end_time - box.start_time).total_seconds() if box.start_time and box.end_time else 0
                    print(f"  [{box.network_id:3d}] {box.name} ({box.host}) - {box.status} - {duration:.0f}s - {box.attempts} attempts")
                    if box.error_output:
                        print(f"        Error preview: {box.error_output[0][:100]}")
                    if box.log_file:
                        print(f"        Log file: {box.log_file}")
            print()

        # Log summary to file
        self.logger.info("="*80)
        self.logger.info(f"Deployment Summary: {success_count} success, {failed_count} failed, {timeout_count} timeout, {error_count} error")
        self.logger.info(f"Total attempts: {total_attempts}, Retried instances: {retried_count}")
        self.logger.info(f"Total duration: {total_duration:.0f}s")
        self.logger.info("="*80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Deploy GOAD across multiple networks in parallel.\n\n'
                    'This script automatically:\n'
                    '  1. Activates all Windows hosts using KMS\n'
                    '  2. Prepares all Kali boxes (pentester user, RDP access, credentials)\n'
                    '  3. Prepares all deployment boxes using Ansible\n'
                    '  4. Deploys GOAD on all boxes simultaneously using threading\n'
                    '  5. Retries failed deployments automatically\n'
                    '  6. Logs all operations for debugging\n'
                    '  7. Saves Kali credentials to ansible/credentials/kali/ for printout',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy with default settings (10 parallel threads, 3 retries)
  # Automatically runs Windows activation, Kali setup, and Ansible preparation first
  ./deploy-goad-threaded.py

  # Deploy with 20 parallel threads and 5 retries
  ./deploy-goad-threaded.py --threads 20 --retries 5

  # Use different inventory file
  ./deploy-goad-threaded.py --inventory /path/to/hosts

  # Use different GOAD provider
  ./deploy-goad-threaded.py --provider vmware

  # Custom log directory
  ./deploy-goad-threaded.py --log-dir /var/log/goad-deployments

Note: The script will automatically run the Ansible playbook to prepare
all deployment boxes before starting GOAD deployments. All output is
logged to the specified log directory.
        """
    )

    parser.add_argument(
        '--inventory',
        default='../inventory/hosts',
        help='Path to Ansible inventory file (default: ../inventory/hosts)'
    )

    parser.add_argument(
        '--threads',
        type=int,
        default=10,
        help='Maximum number of parallel deployments (default: 10)'
    )

    parser.add_argument(
        '--provider',
        default='proxmox',
        choices=['proxmox', 'vmware', 'azure', 'aws'],
        help='GOAD provider to use (default: proxmox)'
    )

    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts for failed deployments (default: 3)'
    )

    parser.add_argument(
        '--log-dir',
        default='./logs',
        help='Directory to store deployment logs (default: ./logs)'
    )

    args = parser.parse_args()

    # Create deployer and run
    deployer = GOADDeployer(
        inventory_file=args.inventory,
        max_threads=args.threads,
        goad_provider=args.provider,
        max_retries=args.retries,
        log_dir=args.log_dir
    )

    deployer.deploy_all()


if __name__ == '__main__':
    main()
