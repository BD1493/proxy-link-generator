# 🛡️ Stealth Proxy (Ghost Mode) Enterprise

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![License](https://img.shields.io/badge/License-Permission--Only-red)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## ⛔ STRICT COPYRIGHT & LEGAL NOTICE

**Copyright © 2026 BD. All Rights Reserved.**

**NOTICE TO ALL USERS:** This software and its source code are the exclusive intellectual property of the owner (BD). No part of this repository may be reproduced, distributed, deployed, or modified without **explicit written permission** from the owner. 

### 📜 Permission-Only Open License (2026)
1. **Usage Restriction**: Unauthorized use, including private or commercial deployment, is a violation of international copyright laws.
2. **Mandatory Approval**: You must receive a signed authorization before any execution of this code.
3. **Enforcement**: We actively monitor for unauthorized deployments. Violators will be subject to immediate DMCA takedowns and legal action.

📝 **REQUEST USAGE PERMISSION HERE:** Official Permission Form- https://forms.gle/j6sjiAs7qfL3Jvnf8

---

## 📖 Technical Overview

This application is a **High-Anonymity Reverse Proxy**. It bridges the gap between a user and a target website by sanitizing the data stream and rotating the exit node (IP) for every individual request.



### Advanced Privacy Mechanisms
* **Base64 URL Obfuscation**: Prevents target URLs from appearing in server logs or network sniffers.
* **DOM Sanitization**: Automatically finds and replaces all `src`, `href`, and `action` attributes.
* **CSS Path Correction**: Uses Regex to find `url()` patterns in stylesheets to prevent "leaks" where the browser might try to bypass the proxy for images.
* **Tab Cloaking**: Injects the proxy session into an `about:blank` page to ensure the browser's internal "Top Sites" and "History" lists remain empty.

---

## 🛠️ Phase 1: Local Setup & IP Verification

Before you upload to the cloud, you must ensure your IP list is high-quality.

1. **Environment Setup**:
   - Install [Python 3.9+](https://www.python.org/downloads/).
   - Open your terminal and install the core engine:
     ```bash
     pip install flask requests beautifulsoup4 gunicorn
     ```

2. **IP Pool Preparation**:
   - Create a file named `proxies.txt`.
   - Paste your list of IPs in `IP:PORT` format (e.g., `123.45.67.89:8080`).

3. **Running the Diagnostic Tool**:
   - Run the checker to remove "dead" nodes:
     ```bash
     python checker.py
     ```
   - This script will generate `valid_proxies.txt`. Delete your old `proxies.txt` and rename this new file to `proxies.txt`.

---

## ☁️ Phase 2: Full Deployment Guide (Render.com)

Render provides a secure, automated environment for this app. Follow these steps exactly:

### 1. Prepare GitHub (The Bridge)
- Create a **Private** repository on [GitHub](https://github.com).
- Upload: `app.py`, `proxies.txt`, `requirements.txt`, and `README.md`.
- **Note**: Never make this repository "Public" as it contains your private IP pool.

### 2. Connect to Render
- Sign in to [Render](https://render.com) using your GitHub account.
- Click the **"New"** button and select **"Web Service"**.
- Locate your `stealth-proxy` repository and click **"Connect"**.

### 3. Detailed Web Service Configuration
Configure the service with these exact specifications:

| Field | Value |
| :--- | :--- |
| **Name** | `security-tunnel-v1` (or your choice) |
| **Region** | Select the region closest to your target audience. |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` (or Starter for higher speeds) |



### 4. Final Activation
- Click **"Create Web Service"**.
- Watch the "Logs" window. You will see "Installing dependencies" followed by "Your service is live."
- Copy the generated URL (e.g., `https://security-tunnel-v1.onrender.com`).

---

## 🚀 How to Use the Stealth Interface

1. **Launch**: Navigate to your Render URL.
2. **Disguise**: The page will appear as a "Google Drive" storage portal.
3. **Input**: Enter the full URL you wish to visit (e.g., `https://wikipedia.org`) into the search bar.
4. **Execution**: Click "Open File".
5. **Observation**: A new browser tab will open. Notice the address bar says `about:blank`. The website will load inside this "Ghost Tab."

---

## 🧩 Troubleshooting & Maintenance

- **IP Failures**: If the page shows "Node Error," refresh the page. This triggers the app to pick a different IP from your `proxies.txt`.
- **Formatting Issues**: If a website looks "broken," the site likely uses complex JavaScript (React/Next.js) that resists proxying.
- **Sleep Mode**: On the Render Free Tier, the app will sleep after 15 minutes of inactivity. The first load after a break may take 30 seconds.

---

## 📜 TERMINATION OF ACCESS

Failure to comply with the **Permission-Only Open License (2026)** will result in:
1. Revocation of all access rights.
2. Mandatory deletion of all source code copies.
3. Reporting of the unauthorized deployment to the hosting provider (Render/GitHub).

---
*Developed by BD. For technical support or permission inquiries, use the linked form.*
