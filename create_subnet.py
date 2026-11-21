"""
Creates a public subnet in an existing VCN for use with Always-Free instances.
"""
import oci
import os
import sys
from dotenv import load_dotenv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(PROJECT_DIR, "oci.env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

CONFIG_FILE = os.getenv("OCI_CONFIG", os.path.join(PROJECT_DIR, "oci_config"))
AD_NAME = os.getenv("OCT_FREE_AD", "").split(",")[0].strip()

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}.")
    sys.exit(1)

config = oci.config.from_file(CONFIG_FILE)
tenancy_id = config["tenancy"]
network_client = oci.core.VirtualNetworkClient(config)

# Find VCN
vcns = network_client.list_vcns(compartment_id=tenancy_id).data
if not vcns:
    print("Error: No VCN found. Please create a Virtual Cloud Network in the OCI Console first.")
    sys.exit(1)

target_vcn = vcns[0]
vcn_id = target_vcn.id
print(f"Using VCN: {target_vcn.display_name} ({vcn_id})")

# 1. Get or create Internet Gateway
print("Checking for Internet Gateway...")
igws = network_client.list_internet_gateways(compartment_id=tenancy_id, vcn_id=vcn_id).data
if igws:
    igw_id = igws[0].id
    print(f"  Found existing Internet Gateway: {igw_id}")
else:
    print("  Creating Internet Gateway...")
    igw = network_client.create_internet_gateway(
        oci.core.models.CreateInternetGatewayDetails(
            compartment_id=tenancy_id,
            vcn_id=vcn_id,
            is_enabled=True,
            display_name="igw-freetier"
        )
    ).data
    igw_id = igw.id
    print(f"  Created: {igw_id}")

# 2. Get default route table and route 0.0.0.0/0 to IGW
print("Updating route table...")
route_tables = network_client.list_route_tables(compartment_id=tenancy_id, vcn_id=vcn_id).data
default_rt = route_tables[0]
network_client.update_route_table(
    default_rt.id,
    oci.core.models.UpdateRouteTableDetails(
        route_rules=[
            oci.core.models.RouteRule(
                destination="0.0.0.0/0",
                destination_type="CIDR_BLOCK",
                network_entity_id=igw_id
            )
        ]
    )
)
print(f"  Route table updated: {default_rt.id}")

# 3. Create subnet
print("Creating public subnet...")
subnet = network_client.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id=tenancy_id,
        vcn_id=vcn_id,
        cidr_block="10.0.0.0/24",
        display_name="subnet-freetier-public",
        route_table_id=default_rt.id,
    )
).data

print(f"\n✅ Subnet created successfully!")
print(f"  Name: {subnet.display_name}")
print(f"  OCID: {subnet.id}")
print(f"\nAdd this to your oci.env:")
print(f"  OCI_SUBNET_ID={subnet.id}")
