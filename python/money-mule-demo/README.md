# FraudGuard - Advanced Fraud Detection System

## Overview

FraudGuard is a fraud detection system powered by Aerospike Graph. It provides advanced money mule detection capabilities with an intuitive React-based dashboard and powerful network visualization tools.

---

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│  Flask Backend   │────│ Aerospike Graph │
│                 │    │                  │    │                 │
│ • Dashboard     │    │ • Fraud Analysis │    │ • Graph Data    │
│ • Network Viz   │    │ • REST APIs      │    │ • Gremlin Query │
│ • Account Details│   │ • Parallel Proc. │    │ • Transactions  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Quick Start

### Prerequisites

- **Node.js**: v16+ 
- **Python**: v3.8+
- **Aerospike Graph**: Running instance with Gremlin endpoint

---

## Start Aerospike Graph and load data 
From the root of the repo
```bash
docker compose up -d 
```

### Create Python Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
```

### Install Python Dependencies
```bash
pip install flask flask-cors gremlinpython
```
### Generate and Load Data

```bash
python3 generate_Data_Main.py
```


```bash
python3 load_data.py
```

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd python/money-mule-demo/backend
```

**Required Python Packages:**
- `flask` - Web framework for REST APIs
- `flask-cors` - CORS support for cross-origin requests
- `gremlinpython` - Aerospike Graph/Gremlin Python driver

### 4. Verify Installation
```bash
python -c "import flask, flask_cors, gremlin_python; print('All dependencies installed!')"
```

### 5. Configure Database Connection
Ensure your Aerospike Graph instance is running and accessible at:
```
ws://localhost:8182/gremlin
```

### 6. Start Backend Server
```bash
python app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd python/money-mule-demo/frontend
```

### 2. Install Node.js Dependencies
```bash
npm install
```

**Key Dependencies Installed:**
- `react` & `react-dom` - Core React framework
- `@mui/material` & `@mui/icons-material` - Material-UI components
- `@emotion/react` & `@emotion/styled` - CSS-in-JS styling
- `react-router-dom` - Client-side routing
- `@visx/network` & `@visx/scale` - Data visualization
- `three` - 3D graphics library

### 3. Start Development Server
```bash
npm start
```

**Expected Output:**
```
Local:            http://localhost:3000
On Your Network:  http://192.168.1.x:3000
```

### 4. Access Application
Open your browser to: **http://localhost:3000**

---

**You're ready to detect fraud with FraudGuard!**

