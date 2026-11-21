# Contributing to Oracle Free Tier Automation

Thank you for considering contributing! We welcome bug fixes, documentation improvements, feature additions, and optimizations.

---

## 🛠️ How to Contribute

1. **Fork the Repository**
   Click the "Fork" button at the top right of this page.

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/<your-username>/oracle-freetier-automation.git
   cd oracle-freetier-automation
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make Your Changes**
   - Ensure clean, idiomatic Python code.
   - Do NOT commit sensitive files (`.pem`, `.env`, keys, tokens).
   - Test your changes using a virtual environment.

5. **Commit Your Changes**
   Follow conventional commits:
   ```bash
   git commit -m "feat: add support for new notification provider"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   Submit a PR against the `main` branch with a clear description of your changes.

---

## 🔒 Security Best Practices

- Never submit PRs containing test API keys, tenancies, or personal credentials.
- Test your `.gitignore` configuration before staging files.
