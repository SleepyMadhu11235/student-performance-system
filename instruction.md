# 🚀 End-to-End Deployment Guide: Student Performance Prediction System

This comprehensive, step-by-step guide will walk you through deploying your fullstack application safely, reliably, and completely on **free tiers**:
- **Frontend**: [Vercel](https://vercel.com) (Global Edge CDN, Automatic HTTPS, Vite SPA)
- **Backend API**: [Render](https://render.com) (Free Cloud Web Service, Python/Django + Gunicorn + WhiteNoise)
- **Database**: [Aiven](https://aiven.io) (Free Cloud-managed MySQL 8 instance with SSL/TLS)

---

## 🏗️ Architecture Overview

```mermaid
flowchart LR
    subgraph Client ["Client Browser"]
        Browser["User Web Browser"]
    end

    subgraph Vercel ["Vercel Edge Network"]
        Frontend["React + Vite Frontend\n(Static Assets + Router Rewrites)"]
    end

    subgraph Render ["Render Cloud (Free Web Service)"]
        Gunicorn["Gunicorn WSGI Server"]
        Django["Django REST Framework\n+ ML Pipeline (Scikit-Learn)"]
        WhiteNoise["WhiteNoise Static Engine"]
    end

    subgraph Aiven ["Aiven Cloud Database"]
        MySQL[("MySQL 8 Service\n(Enforced TLS / SSL)")]
    end

    Browser -->|"Loads UI (HTTPS)"| Frontend
    Browser -->|"API Calls (/api/*)"| Gunicorn
    Gunicorn --> Django
    Django --> WhiteNoise
    Django -->|"Encrypted SQL (Port 10000-30000)"| MySQL
```

---

## 📋 Prerequisites Checklist

Before you begin, ensure you have free accounts on:
1. **GitHub**: [github.com](https://github.com) (where your repository is hosted)
2. **Aiven**: [console.aiven.io](https://console.aiven.io) (for managed MySQL)
3. **Render**: [dashboard.render.com](https://dashboard.render.com) (for Python/Django backend hosting)
4. **Vercel**: [vercel.com](https://vercel.com) (for React frontend hosting)

---

## Part 1: Set Up MySQL on Aiven (Free Tier)

Aiven provides cloud-managed MySQL instances with built-in backups and strict SSL encryption.

### Step 1.1: Create your MySQL Service
1. Log in to [Aiven Console](https://console.aiven.io).
2. Click **Create Service** (or **+ Add Service**).
3. Select **MySQL**.
4. Choose a Cloud Provider and Region:
   - **Provider**: AWS or Google Cloud (either works).
   - **Region**: Choose a region geographically close to you or Frankfurt / Virginia (e.g. `aws-eu-central-1` or `aws-us-east-1`).
5. Select the **Free Plan** (or the lowest tier / free trial plan).
6. Give your service a name, e.g.: `student-mysql-db`.
7. Click **Create Service**.

### Step 1.2: Gather Connection Credentials
1. Wait 2–3 minutes until the service status turns from *Rebuilding* to **Running** (green indicator).
2. On the **Overview** page under **Connection information**, keep this tab open or copy the following details:

| Field Name | Typical Example Value | What to do |
| :--- | :--- | :--- |
| **Host** | `mysql-xxxxxx.aivencloud.com` | Copy this hostname |
| **Port** | `24589` (a 5-digit port) | Copy this port number |
| **User** | `avnadmin` | Default admin user |
| **Password** | *(Click the eye icon to reveal)* | Copy this secret password |
| **Database** | `defaultdb` | Default database name |
| **Service URI** | `mysql://avnadmin:pass@host:port/defaultdb?ssl-mode=REQUIRED` | Copy (can be used as `DATABASE_URL`) |

> [!NOTE]
> **SSL Encryption Handshake**: Aiven enforces TLS/SSL. The backend codebase has been configured to automatically negotiate secure TLS with Aiven without crashing or requiring manual CA uploads. If you want strict CA pinning, you can also download the **CA Certificate** (`ca.pem`) from the Aiven overview page.

---

## Part 2: Commit and Push Code Changes to GitHub

The required deployment configurations (WhiteNoise static serving, Gunicorn, Aiven SSL support, Vercel SPA rewrites, and build scripts) have been prepared in your codebase.

Open PowerShell or terminal in your project root:
`c:\Users\Madhu\Downloads\student-performance-system-FINAL\student-performance-system`

Run the following commands:

```powershell
# 1. Check changed files
git status

# 2. Stage all modifications and new deployment configuration files
git add .

# 3. Commit the changes
git commit -m "Configure production deployment for Vercel, Render, and Aiven MySQL"

# 4. Push to your GitHub main branch
git push origin main
```

---

## Part 3: Deploy Backend on Render (Free Web Service)

Render will host the Django REST API and run machine learning predictions.

### Step 3.1: Create Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click the **+ New** button in the top navigation bar and select **Web Service**.
3. Under **Connect a Git repository**, find your repository:
   - Select `student-performance-system` (or click *Connect account* if not visible yet).
4. Fill in the service configuration details:

| Setting | Value to Enter / Select | Why it matters |
| :--- | :--- | :--- |
| **Name** | `student-performance-backend` | Appears in your Render URL |
| **Region** | Choose nearest to your Aiven DB (e.g. Frankfurt or Oregon) | Minimizes database query latency |
| **Branch** | `main` | Production branch |
| **Root Directory** | `backend` | **CRITICAL**: Tells Render Django is in `/backend` |
| **Runtime** | `Python 3` | Native Python runtime |
| **Build Command** | `./build.sh` | Installs packages, runs `collectstatic`, runs `migrate` |
| **Start Command** | `gunicorn config.wsgi:application` | Production WSGI application server |
| **Instance Type** | **Free** | \$0 / month tier |

> [!TIP]
> If `./build.sh` ever gives a permission warning, you can alternatively enter this single line in **Build Command**:
> ```bash
> pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
> ```

### Step 3.2: Configure Environment Variables in Render
Scroll down to the **Environment Variables** section and click **Add Environment Variable** for each of the following:

| Key | Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures pre-built scikit-learn & numpy wheels install quickly |
| `DJANGO_DEBUG` | `False` | Disables debug mode for secure production |
| `DJANGO_SECRET_KEY` | *(Click "Generate" or enter 50 random chars)* | Cryptographic security key |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com,localhost,127.0.0.1` | Allows Render URLs and local testing |
| `DB_ENGINE` | `mysql` | Activates MySQL backend |
| `DB_HOST` | `your-host.aivencloud.com` | Paste the **Host** from Aiven |
| `DB_PORT` | `24589` | Paste the **Port** from Aiven |
| `DB_USER` | `avnadmin` | Paste the **User** from Aiven |
| `DB_PASSWORD` | `your_aiven_password` | Paste the **Password** from Aiven |
| `DB_NAME` | `defaultdb` | Paste the **Database** name from Aiven |
| `CORS_ALLOW_VERCEL_PREVIEWS` | `True` | Automatically permits all `*.vercel.app` frontend calls |

*(Alternative)*: Instead of `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, you can simply add a single variable:
- `DATABASE_URL`: `mysql://avnadmin:your_password@your-host.aivencloud.com:port/defaultdb?ssl-mode=REQUIRED`

### Step 3.3: Deploy and Verify
1. Click **Create Web Service**.
2. Watch the deployment logs in real time. You will see:
   - Dependencies installing (`pip install -r requirements.txt`)
   - Static files collecting (`collectstatic`)
   - Migrations applying to Aiven (`Applying predictions.0001_initial... OK`)
   - `Gunicorn running on http://0.0.0.0:10000`
   - Service status turns to **Live** with a green badge.
3. Test your backend:
   - At the top left of the Render service page, click your URL (e.g. `https://student-performance-backend.onrender.com`).
   - You should see the operational response:
     ```json
     {
       "status": "ok",
       "service": "student-performance-system-backend",
       "message": "Student Performance Prediction API is running successfully."
     }
     ```
4. **Copy this backend URL**. You will need it in the next step!

---

## Part 4: Deploy Frontend on Vercel

Vercel will compile and host your React + Vite application with global edge routing.

### Step 4.1: Import Project into Vercel
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Locate `student-performance-system` from your GitHub account and click **Import**.

### Step 4.2: Configure Build & Environment Settings
1. **Framework Preset**: Verify it detects **Vite** (if not, select `Vite` from the dropdown).
2. **Root Directory**:
   - Click the **Edit** button next to Root Directory.
   - Select the `frontend` folder and click **Continue**.
3. **Build and Output Settings**:
   - Leave defaults unchanged (`npm run build` and `dist`).
4. **Environment Variables**:
   - Expand the **Environment Variables** section.
   - Add:
     - **Name**: `VITE_API_BASE_URL`
     - **Value**: `https://<your-render-backend-url>.onrender.com/api`
     *(Example: `https://student-performance-backend.onrender.com/api`)*

> [!IMPORTANT]
> Make sure to include `/api` at the end of the URL (our code also automatically checks and appends `/api` if omitted, but best practice is to supply it directly).

### Step 4.3: Deploy
1. Click **Deploy**.
2. Vercel will install dependencies and compile the production build in ~30–45 seconds.
3. Click **Continue to Dashboard** or visit your live domain (e.g. `https://student-performance-system-xxx.vercel.app`).

### Step 4.4: (Recommended) Sync CORS in Render
To ensure the highest security standard:
1. Go back to your [Render Dashboard](https://dashboard.render.com).
2. Click into `student-performance-backend` -> **Environment**.
3. Add or update:
   - `CORS_ALLOWED_ORIGINS` = `https://your-frontend-domain.vercel.app`
4. Click **Save Changes** (Render will automatically re-deploy in a few seconds).

---

## Part 5: Complete Verification Checklist

Perform these sanity tests to ensure all systems are communicating smoothly:

- [ ] **1. Dashboard Page (`/`)**:
  - Open your Vercel URL.
  - The metrics cards (Total Predictions, Pass Rate, Avg Confidence) and charts should load without network errors.
- [ ] **2. Single Student Prediction (`/predict`)**:
  - Enter test scores (e.g. Attendance: `85`, Midterm 1: `78`, Midterm 2: `82`, Assignments: `90`, Study Hours: `12`).
  - Click **Predict Performance**.
  - A predicted badge (e.g., `Good` or `Excellent`), probability distribution, and rule-based explanation will appear immediately.
- [ ] **3. Historical Ledger (`/history`)**:
  - Check the History tab. The prediction made in step 2 should appear in the table with its timestamp, saved in your Aiven MySQL database.
  - Test the filter dropdown (e.g. filter by `Fail` or `Pass`).
- [ ] **4. Export CSV**:
  - On the History page, click **Export CSV**.
  - A CSV file containing the predictions will download to your machine.
- [ ] **5. ML Models Tab (`/models`)**:
  - Click the **Models** tab in the navigation bar.
  - View the four-way algorithmic comparison (Random Forest, Decision Tree, Naive Bayes, KNN) with precision/recall/F1 metrics.
- [ ] **6. SPA Route Refresh**:
  - Navigate to `/predict` or `/history` and refresh your browser (`Ctrl + F5`).
  - The page will re-render seamlessly without 404 errors (thanks to `frontend/vercel.json`).

---

## 🛠️ Troubleshooting & Frequently Asked Questions

### 1. Render Free Tier "Cold Start" (Spin-Down)
- **What happens**: Render's free web services automatically spin down into a sleep state after 15 minutes of inactivity.
- **Symptom**: The first API call after a period of inactivity may take 30–50 seconds to respond.
- **Built-in Protection**: We increased the frontend request timeout to **60 seconds** in `client.js` so it won't prematurely error while Render is spinning up.
- **Tip to keep it awake**: You can use a free uptime monitoring service like [UptimeRobot](https://uptimerobot.com) or [cron-job.org](https://cron-job.org) to ping your health endpoint (`https://<your-backend>.onrender.com/health`) every 10 minutes.

### 2. Database Connection Error or `unexpected keyword argument 'ssl-mode'`
- **What happened**: When using Aiven's Service URI (`mysql://avnadmin:pass@host:port/defaultdb?ssl-mode=REQUIRED`), `dj-database-url` extracts `?ssl-mode=REQUIRED` into Django's database `OPTIONS`. PyMySQL does not accept hyphens in `ssl-mode` and expects `ssl` object directly.
- **The Fix**: Our updated `settings.py` automatically detects and strips `ssl-mode` from `OPTIONS` while keeping Python's TLS encryption handshake active.
- Ensure your Aiven service status is **Running** in green.
- Verify that `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in Render match Aiven's connection card exactly.
- Make sure `DB_PORT` is the exact 5-digit port specified by Aiven (NOT default `3306`).
- If you use `DATABASE_URL`, ensure special characters in your password are properly URL-encoded or use discrete variables (`DB_PASSWORD`).

### 3. Vercel SPA shows 404 on page refresh
- If navigating to `/predict` directly returns 404, verify that `frontend/vercel.json` is committed in git and located in the `frontend` root directory with the rewrite rule to `/index.html`.

### 4. How to re-run migrations manually on Render
If you ever change models and need to execute migrations manually:
1. Open your Web Service in Render.
2. Click **Shell** in the left sidebar.
3. Type:
   ```bash
   python manage.py migrate
   ```
4. Press Enter.

---

🎉 **Congratulations!** Your complete machine learning web application is now successfully running in production on Vercel, Render, and Aiven MySQL!
