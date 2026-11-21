# Oracle Free Tier Automation — Command Reference

A quick-reference sheet for managing your OCI instance creation sniper, both on your local machine and on a dedicated cloud runner.

---

## 📁 Key File Locations

| Item | Purpose |
|------|---------|
| `oci_config` | OCI API connection details (user, tenancy, fingerprint, key_file) |
| `oci.env` | Automation environment settings (shapes, retries, notifications) |
| `id_rsa_private` | Generated SSH private key used to access created instances |
| `id_rsa.pub` | Generated SSH public key injected into instances |
| `launch_instance.log` | Real-time log of every OCI provisioning attempt |
| `INSTANCE_CREATED` | Auto-generated when the instance is successfully created |

---

## ☁️ Cloud Runner (24/7 on Free Micro Instance)

Running the script on an Always-Free `VM.Standard.E2.1.Micro` instance allows 24/7 background operation without keeping your personal laptop awake.

### SSH into the Runner
```bash
ssh ubuntu@<RUNNER_IP> -i path/to/id_rsa_private
```

### Script Management (Inside the VM)

```bash
# Check if the screen session is active
screen -ls

# View live output / attach to session
screen -r oracle
# (To detach without killing the process: press Ctrl+A then D)

# Start / Restart in background screen session
cd ~/oracle-freetier-automation
screen -dmS oracle bash setup_init.sh rerun

# Stop the runner process
screen -S oracle -X quit
```

### Viewing Logs
```bash
# Real-time creation attempts
tail -f ~/oracle-freetier-automation/launch_instance.log

# Diagnostic and setup information
cat ~/oracle-freetier-automation/setup_and_info.log

# Verify success
cat ~/oracle-freetier-automation/INSTANCE_CREATED
```

---

## 🔒 Security & Hardening Commands

Ensure your runner host is hardened against unauthorized access:

```bash
# Check UFW firewall status
sudo ufw status verbose

# Check fail2ban SSH jail and banned IPs
sudo fail2ban-client status sshd

# View recent banned IPs
sudo fail2ban-client get sshd banip --with-time

# Check active connections
ss -tnp
who

# Check CPU usage (verify no rogue miners)
top -bn1 | head -20
ps aux --sort=-%cpu | head -10
```

---

## ⏰ Periodic Status Reports (Telegram)

The included `send_status_update.py` script sends automated progress digests to your Telegram chat.

```bash
# Trigger a report manually
python3 ~/oracle-freetier-automation/send_status_update.py

# Add to crontab to run every 2 hours:
# (crontab -e)
0 */2 * * * /usr/bin/python3 /home/ubuntu/oracle-freetier-automation/send_status_update.py >> /home/ubuntu/status_cron.log 2>&1
```

---

## 🖥️ Local Machine (macOS launchd service)

If running directly on your Mac:

```bash
# Start background service
launchctl load ~/Library/LaunchAgents/com.oracle.freetier.plist

# Stop background service
launchctl unload ~/Library/LaunchAgents/com.oracle.freetier.plist

# Check status
launchctl list | grep oracle

# Run manually in foreground
bash setup_init.sh rerun
```

---

## 🎯 Interpreting Logs

- **`500 InternalError: Out of host capacity`**  
  *Normal and expected.* Oracle currently has no free hardware in this shape/AD. The script will wait `REQUEST_WAIT_TIME_SECS` and retry automatically.

- **`429 TooManyRequests: Too many requests for the tenant`**  
  *Rate limited.* Your wait time is too aggressive or multiple instances of the script are running simultaneously. Increase `REQUEST_WAIT_TIME_SECS` to 75–90s.
