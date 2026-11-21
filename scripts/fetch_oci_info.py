"""
Helper script to discover Availability Domains, VCNs, and Subnets in your OCI tenancy.
"""
import oci
import os
import sys
from dotenv import load_dotenv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
ENV_FILE = os.path.join(PROJECT_DIR, "oci.env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

CONFIG_FILE = os.getenv("OCI_CONFIG", os.path.join(PROJECT_DIR, "oci_config"))

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}. Refer to oci_config.example.")
    sys.exit(1)

config = oci.config.from_file(CONFIG_FILE)
tenancy_id = config["tenancy"]

identity_client = oci.identity.IdentityClient(config)
network_client = oci.core.VirtualNetworkClient(config)

# Availability Domains
ads = identity_client.list_availability_domains(compartment_id=tenancy_id).data
print("=== AVAILABILITY DOMAINS ===")
for ad in ads:
    print(f"  {ad.name}")

# VCNs and Subnets
print("\n=== VCNs and SUBNETS ===")
compartments = identity_client.list_compartments(
    compartment_id=tenancy_id, compartment_id_in_subtree=True
).data
all_compartments = [tenancy_id] + [c.id for c in compartments if c.lifecycle_state == "ACTIVE"]

for cid in all_compartments:
    try:
        vcns = network_client.list_vcns(compartment_id=cid).data
        for vcn in vcns:
            print(f"\n  VCN: {vcn.display_name} ({vcn.id})")
            subnets = network_client.list_subnets(compartment_id=cid, vcn_id=vcn.id).data
            for s in subnets:
                print(f"    Subnet: {s.display_name}")
                print(f"    OCID:   {s.id}")
                print(f"    AD:     {s.availability_domain or 'Regional'}")
    except Exception:
        pass
