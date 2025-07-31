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

## Alternative Package Managers

### Using Yarn (Frontend)
```bash
cd python/money-mule-demo/frontend
yarn install
yarn start
```

### Using Conda (Backend)
```bash
cd python/money-mule-demo/backend
conda create -n fraudguard python=3.9
conda activate fraudguard
conda install flask flask-cors
pip install gremlinpython  # Not available in conda
python app.py
```

---

## Docker Setup (Optional)

### Backend Dockerfile
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Frontend Dockerfile
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

---

## System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **CPU**: 2 cores
- **Storage**: 1GB free space
- **Network**: Broadband connection

### Recommended Requirements
- **RAM**: 8GB+
- **CPU**: 4+ cores
- **Storage**: 5GB+ free space
- **Network**: High-speed broadband

---

## Testing Installation

### Backend Health Check
```bash
curl http://localhost:5000/api/stats
```

**Expected Response:**
```json
{
  "totalAccounts": 1000,
  "suspiciousPatterns": 23,
  "highRiskAlerts": 23,
  "monitoringAlerts": 34
}
```

### Frontend Verification
1. Navigate to **http://localhost:3000**
2. Click **"Find Suspicious Accounts"**
3. Verify suspicious accounts are displayed
4. Click on an account to test fraud analysis
5. Click **"View Network Analysis"** to test visualization

---

## Troubleshooting

### Common Backend Issues

**Connection Error:**
```
Error: Database connection failed
```
**Solution:** Verify Aerospike Graph is running on `localhost:8182`

**Import Error:**
```
ModuleNotFoundError: No module named 'flask'
```
**Solution:** Activate virtual environment and reinstall dependencies

### Common Frontend Issues

**Module Not Found:**
```
Module not found: Error: Can't resolve '@mui/material'
```
**Solution:** Delete `node_modules` and run `npm install` again

**Port Already in Use:**
```
Something is already running on port 3000
```
**Solution:** Kill existing process or use different port: `PORT=3001 npm start`

---

## Performance Tuning

### Backend Optimization
```python
# In Structured_Mule_Activity.py
detect_structured_mule_activity(max_workers=8)  # Adjust based on CPU cores
```

### Frontend Optimization
```javascript
// In Dashboard.js
const CACHE_EXPIRY_HOURS = 2;  # Adjust cache duration
```

---

## Security Considerations

- **Environment Variables**: Store sensitive config in `.env` files
- **CORS**: Configure appropriate origins for production
- **Authentication**: Add authentication layer for production use
- **HTTPS**: Use SSL/TLS certificates in production

---

## Development Commands

### Backend
```bash
# Run with debug mode
python app.py

# Run tests (if available)
python -m pytest

# Check code style
flake8 *.py
```

### Frontend
```bash
# Development server
npm start

# Production build
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For issues and questions:
- **GitHub Issues**: Create an issue in the repository
- **Documentation**: Check this README and code comments
- **Aerospike Support**: Visit Aerospike documentation for graph database issues

---

## Next Steps After Installation

1. **Load Sample Data**: Import transaction data into Aerospike Graph
2. **Configure Detection Rules**: Customize fraud detection scenarios
3. **Set Up Monitoring**: Configure alerts and notifications
4. **Performance Testing**: Test with your expected data volume
5. **Production Deployment**: Follow security best practices

---

**You're ready to detect fraud with FraudGuard!**

