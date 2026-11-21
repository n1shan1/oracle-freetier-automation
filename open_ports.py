"""
Opens port 22 (SSH), 80 (HTTP), and 443 (HTTPS) in the VCN default security list,
and checks connection to the instance.
"""
import oci
import os
import sys
import socket
import time
from dotenv import load_dotenv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(PROJECT_DIR, "oci.env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

CONFIG_FILE = os.getenv("OCI_CONFIG", os.path.join(PROJECT_DIR, "oci_config"))
INSTANCE_IP = sys.argv[1] if len(sys.argv) > 1 else os.getenv("RUNNER_IP", "")

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}.")
    sys.exit(1)

config = oci.config.from_file(CONFIG_FILE)
tenancy_id = config["tenancy"]
network_client = oci.core.VirtualNetworkClient(config)

# Find VCNs in compartment
vcns = network_client.list_vcns(compartment_id=tenancy_id).data
if not vcns:
    print("No VCNs found in tenancy.")
    sys.exit(1)

for vcn in vcns:
    sec_lists = network_client.list_security_lists(compartment_id=tenancy_id, vcn_id=vcn.id).data
    for sl in sec_lists:
        print(f"Checking Security List: {sl.display_name}")
        existing_rules = sl.ingress_security_rules
        existing_ports = [
            r.tcp_options.destination_port_range.min
            for r in existing_rules
            if r.protocol == "6" and r.tcp_options and r.tcp_options.destination_port_range
        ]
        
        new_rules = list(existing_rules)
        for port, desc in [(22, "SSH"), (80, "HTTP"), (443, "HTTPS")]:
            if port not in existing_ports:
                print(f"  Opening port {port} ({desc})...")
                new_rules.append(oci.core.models.IngressSecurityRule(
                    protocol="6",
                    source="0.0.0.0/0",
                    is_stateless=False,
                    tcp_options=oci.core.models.TcpOptions(
                        destination_port_range=oci.core.models.PortRange(min=port, max=port)
                    )
                ))
            else:
                print(f"  Port {port} is already open.")

        network_client.update_security_list(
            sl.id,
            oci.core.models.UpdateSecurityListDetails(ingress_security_rules=new_rules)
        )

if INSTANCE_IP:
    print(f"\nWaiting for SSH on {INSTANCE_IP}:22 ...")
    for i in range(20):
        try:
            s = socket.create_connection((INSTANCE_IP, 22), timeout=5)
            s.close()
            print("✅ SSH port is reachable!")
            break
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"  Not ready yet ({i+1}/20), retrying in 10s...")
            time.sleep(10)
