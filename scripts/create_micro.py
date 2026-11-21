"""
Automated helper to launch an Always-Free Micro (VM.Standard.E2.1.Micro) instance
to act as the 24/7 sniper host for ARM capacity.
"""
import oci
import os
import sys
import time
from dotenv import load_dotenv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
ENV_FILE = os.path.join(PROJECT_DIR, "oci.env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

CONFIG_FILE = os.getenv("OCI_CONFIG", os.path.join(PROJECT_DIR, "oci_config"))
SUBNET_ID = os.getenv("OCI_SUBNET_ID", "").strip()
AD_NAME = os.getenv("OCT_FREE_AD", "").split(",")[0].strip()
SHAPE = "VM.Standard.E2.1.Micro"
SSH_KEY_FILE = os.getenv("SSH_AUTHORIZED_KEYS_FILE", os.path.join(PROJECT_DIR, "id_rsa.pub"))

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}. Refer to oci_config.example.")
    sys.exit(1)

if not SUBNET_ID:
    print("Error: OCI_SUBNET_ID is required in oci.env to launch a micro instance.")
    sys.exit(1)

config = oci.config.from_file(CONFIG_FILE)
tenancy_id = config["tenancy"]

compute_client = oci.core.ComputeClient(config)
network_client = oci.core.VirtualNetworkClient(config)

# Ensure SSH key exists
if not os.path.exists(SSH_KEY_FILE):
    print(f"SSH public key not found at {SSH_KEY_FILE}. Please generate one or run setup_init.sh first.")
    sys.exit(1)

with open(SSH_KEY_FILE, "r") as f:
    ssh_public_key = f.read().strip()

# Find latest Ubuntu 22.04 image for this shape
print("Finding Ubuntu 22.04 image for E2.1.Micro...")
images = compute_client.list_images(
    compartment_id=tenancy_id,
    shape=SHAPE,
    operating_system="Canonical Ubuntu",
    operating_system_version="22.04",
    sort_by="TIMECREATED",
    sort_order="DESC"
).data

if not images:
    print("No Ubuntu 22.04 image found for this shape!")
    sys.exit(1)

image = images[0]
print(f"  Using Image: {image.display_name} ({image.id})")

# Launch the instance
print("\nLaunching Micro instance...")
response = compute_client.launch_instance(
    launch_instance_details=oci.core.models.LaunchInstanceDetails(
        availability_domain=AD_NAME,
        compartment_id=tenancy_id,
        display_name="micro-ubuntu-runner",
        shape=SHAPE,
        create_vnic_details=oci.core.models.CreateVnicDetails(
            assign_public_ip=True,
            subnet_id=SUBNET_ID,
            display_name="micro-ubuntu-runner",
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            source_type="image",
            image_id=image.id,
            boot_volume_size_in_gbs=50,
        ),
        metadata={"ssh_authorized_keys": ssh_public_key},
        availability_config=oci.core.models.LaunchInstanceAvailabilityConfigDetails(
            recovery_action="RESTORE_INSTANCE"
        ),
    )
).data

instance_id = response.id
print(f"  Instance ID: {instance_id}")
print("  Waiting for instance to become RUNNING...")

# Poll until RUNNING
while True:
    instance = compute_client.get_instance(instance_id).data
    state = instance.lifecycle_state
    print(f"  State: {state}")
    if state == "RUNNING":
        break
    elif state in ("TERMINATED", "TERMINATING", "STOPPING"):
        print("Instance launch failed!")
        sys.exit(1)
    time.sleep(10)

# Get public IP
vnics = compute_client.list_vnic_attachments(compartment_id=tenancy_id, instance_id=instance_id).data
vnic = network_client.get_vnic(vnics[0].vnic_id).data

print(f"\n✅ Micro instance is RUNNING!")
print(f"  Name:      {instance.display_name}")
print(f"  Public IP: {vnic.public_ip}")
print(f"\nSSH command:")
print(f"  ssh ubuntu@{vnic.public_ip} -i id_rsa_private")
