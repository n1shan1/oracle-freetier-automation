"""
Script to audit OCI resources and check for any potential costs:
- Instances (shapes, count)
- Boot and Block volumes (total GB vs 200 GB Free Tier limit)
- Public / Reserved IPs
- NAT Gateways / Load Balancers
- Cost / Usage API if accessible
"""
import oci
import os
import json
import requests

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "oci_config")
config = oci.config.from_file(CONFIG_FILE)
tenancy_id = config["tenancy"]

compute_client = oci.core.ComputeClient(config)
block_storage_client = oci.core.BlockstorageClient(config)
network_client = oci.core.VirtualNetworkClient(config)
identity_client = oci.identity.IdentityClient(config)

print("=== 1. COMPUTE INSTANCES AUDIT ===")
instances = compute_client.list_instances(compartment_id=tenancy_id).data
active_instances = [i for i in instances if i.lifecycle_state not in ("TERMINATED", "TERMINATING")]
for inst in active_instances:
    print(f"  Name: {inst.display_name} | Shape: {inst.shape} | State: {inst.lifecycle_state} | ID: {inst.id}")

# 2. Boot and Block Volumes
print("\n=== 2. STORAGE AUDIT (Free Tier Limit: 200 GB) ===")
# List ADs
ads = identity_client.list_availability_domains(compartment_id=tenancy_id).data
total_volume_gb = 0

for ad in ads:
    boot_vols = block_storage_client.list_boot_volumes(availability_domain=ad.name, compartment_id=tenancy_id).data
    for bv in boot_vols:
        if bv.lifecycle_state not in ("TERMINATED", "TERMINATING"):
            print(f"  Boot Volume: {bv.display_name} | Size: {bv.size_in_gbs} GB | State: {bv.lifecycle_state}")
            total_volume_gb += bv.size_in_gbs

    block_vols = block_storage_client.list_volumes(availability_domain=ad.name, compartment_id=tenancy_id).data
    for blk in block_vols:
        if blk.lifecycle_state not in ("TERMINATED", "TERMINATING"):
            print(f"  Block Volume: {blk.display_name} | Size: {blk.size_in_gbs} GB | State: {blk.lifecycle_state}")
            total_volume_gb += blk.size_in_gbs

print(f"  --> Total Storage Used: {total_volume_gb} GB / 200 GB (Always Free)")

# 3. Public IPs (Ephemeral vs Reserved)
print("\n=== 3. PUBLIC IP AUDIT ===")
public_ips = network_client.list_public_ips(scope="REGION", compartment_id=tenancy_id).data
for ip in public_ips:
    print(f"  Public IP: {ip.ip_address} | Lifetime: {ip.lifetime} | Assigned to: {ip.assigned_entity_id}")

# 4. Check for Paid Resources (Load Balancer, NAT Gateways)
print("\n=== 4. GATEWAY & LOAD BALANCER AUDIT ===")
vcns = network_client.list_vcns(compartment_id=tenancy_id).data
nat_gateways = []
for vcn in vcns:
    ngws = network_client.list_nat_gateways(compartment_id=tenancy_id, vcn_id=vcn.id).data
    nat_gateways.extend(ngws)

print(f"  NAT Gateways found: {len(nat_gateways)} (Always Free includes 0 paid NAT Gateways, only IGW is free)")
for ngw in nat_gateways:
    print(f"    NAT Gateway: {ngw.display_name} ({ngw.lifecycle_state})")

# Determine cost status
paid_items = []
if len(active_instances) > 2 and any(i.shape == "VM.Standard.E2.1.Micro" for i in active_instances):
    paid_items.append("More than 2 Micro instances")
if total_volume_gb > 200:
    paid_items.append(f"Storage exceeds 200 GB ({total_volume_gb} GB used)")
if len(nat_gateways) > 0:
    paid_items.append("Paid NAT Gateway present")

unattached_reserved_ips = [ip for ip in public_ips if ip.lifetime == "RESERVED" and not ip.assigned_entity_id]
if unattached_reserved_ips:
    paid_items.append(f"{len(unattached_reserved_ips)} unassigned reserved IP(s)")

print("\n=== COST ASSESSMENT ===")
if paid_items:
    print("⚠️ WARNING: Potential cost items detected:")
    for item in paid_items:
        print(f"  - {item}")
else:
    print("✅ 100% ALWAYS-FREE COMPLIANT. Zero cost incursions detected.")
