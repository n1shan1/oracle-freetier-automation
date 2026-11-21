#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Free Tier Runner - Security Hardening Script
# ==============================================================================
# Applies production security baseline to protect against brute-force attacks,
# unauthorized logins, and crypto-miners on Always-Free Ubuntu VMs.
# ==============================================================================

set -e

echo "🔒 [1/6] Updating system packages..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y -q
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q

echo "🔒 [2/6] Installing security tools (UFW, Fail2ban, Unattended-Upgrades)..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q ufw fail2ban unattended-upgrades

echo "🔒 [3/6] Hardening SSH daemon configuration..."
sudo tee /etc/ssh/sshd_config.d/99-hardened.conf > /dev/null << 'EOF'
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
AllowTcpForwarding no
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
EOF
sudo systemctl reload ssh

echo "🔒 [4/6] Configuring UFW firewall (deny all incoming except SSH port 22)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw --force enable

echo "🔒 [5/6] Enabling Fail2ban (3 failed attempts = 24hr ban)..."
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
maxretry = 3
bantime = 24h
EOF
sudo systemctl enable --now fail2ban
sudo systemctl restart fail2ban

echo "🔒 [6/6] Applying kernel network hardening (sysctl)..."
sudo tee /etc/sysctl.d/99-hardened.conf > /dev/null << 'EOF'
net.ipv4.ip_forward = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
EOF
sudo sysctl -p /etc/sysctl.d/99-hardened.conf > /dev/null 2>&1

echo "🔒 [Bonus] Disabling unused rpcbind service..."
sudo systemctl stop rpcbind rpcbind.socket 2>/dev/null || true
sudo systemctl disable rpcbind rpcbind.socket 2>/dev/null || true

echo ""
echo "============================================="
echo "🛡️ Security Hardening Complete!"
echo "============================================="
echo "UFW Firewall:"
sudo ufw status
echo ""
echo "Fail2ban SSH Jail:"
sudo fail2ban-client status sshd
