# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Reporting a Vulnerability

Security is a top priority for this project. If you discover a security vulnerability or potential credential leak:

1. **Do NOT open a public GitHub issue.**
2. Send an advisory via GitHub Security Advisories or contact the project maintainer directly via GitHub profile: [@n1shan1](https://github.com/n1shan1).
3. Include detailed steps to reproduce the issue and any relevant logs (ensure all keys/credentials are redacted).
4. You will receive an acknowledgment within 48 hours.

---

## User Responsibility

- This tool requires OCI API private keys and credentials.
- **NEVER** commit your `oci_config`, `.pem` private keys, or `oci.env` files to public repositories.
- Always verify that `.gitignore` is actively protecting your private assets before executing `git add .` or pushing changes.
