import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Alert,
  Card,
  CardContent,
  Chip,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ErrorOutline as ErrorIcon,
  AccountTree as NetworkIcon
} from '@mui/icons-material';

const API_BASE_URL = 'http://localhost:5000/api';

// Cache configuration
const CACHE_KEY = 'suspicious_accounts_cache';
const CACHE_EXPIRY_HOURS = 2; // Cache expires after 2 hours

function Dashboard() {
  const navigate = useNavigate();
  const [suspiciousAccounts, setSuspiciousAccounts] = useState([]);
  const [error, setError] = useState(null);
  const [fraudDetails, setFraudDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cacheInfo, setCacheInfo] = useState(null);

  // Load cached data on component mount
  useEffect(() => {
    loadCachedData();
  }, []);

  const loadCachedData = () => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const parsedCache = JSON.parse(cached);
        const now = new Date().getTime();
        const cacheAge = now - parsedCache.timestamp;
        const cacheAgeHours = cacheAge / (1000 * 60 * 60);
        
        if (cacheAgeHours < CACHE_EXPIRY_HOURS) {
          setSuspiciousAccounts(parsedCache.data || []);
          setCacheInfo({
            age: cacheAgeHours,
            count: parsedCache.data?.length || 0,
            timestamp: new Date(parsedCache.timestamp)
          });
          console.log(`Loaded ${parsedCache.data?.length || 0} accounts from cache (${cacheAgeHours.toFixed(1)}h old)`);
        } else {
          // Cache expired, clear it
          localStorage.removeItem(CACHE_KEY);
          setCacheInfo(null);
          console.log('Cache expired, cleared old data');
        }
      }
    } catch (err) {
      console.error('Error loading cached data:', err);
      localStorage.removeItem(CACHE_KEY);
    }
  };

  const saveCacheData = (accounts) => {
    try {
      const cacheData = {
        data: accounts,
        timestamp: new Date().getTime()
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
      setCacheInfo({
        age: 0,
        count: accounts.length,
        timestamp: new Date()
      });
      console.log(`Cached ${accounts.length} suspicious accounts`);
    } catch (err) {
      console.error('Error saving cache data:', err);
    }
  };

  const clearCache = () => {
    localStorage.removeItem(CACHE_KEY);
    setCacheInfo(null);
    setSuspiciousAccounts([]);
    setFraudDetails(null);
    console.log('Cache cleared');
  };

  const findSuspiciousAccounts = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/detect-suspicious-accounts`);
      if (!response.ok) {
        throw new Error('Failed to detect suspicious accounts');
      }
      const data = await response.json();
      const accounts = data.accounts || [];
      setSuspiciousAccounts(accounts);
      
      // Save to cache
      saveCacheData(accounts);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAccountClick = async (accountId) => {
    try {
      setError(null);
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/fraud-scenario/${accountId}`);
      if (!response.ok) {
        throw new Error('Failed to run fraud scenario');
      }
      const data = await response.json();
      setFraudDetails(data.details);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderFraudDetails = () => {
    if (!fraudDetails) return null;

    if (fraudDetails.error) {
      return (
        <Alert severity="error" sx={{ mt: 3 }}>
          {fraudDetails.error}
        </Alert>
      );
    }

    const detectedScenarios = Object.entries(fraudDetails.scenarios || {})
      .filter(([_, scenario]) => scenario.detected);

    if (detectedScenarios.length === 0) {
      return (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="h6" color="success.main">
                Account Analysis Complete
              </Typography>
            </Box>
            <Typography variant="body1">
              Account {fraudDetails.account_number} appears to be clean - no suspicious fraud patterns detected.
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<NetworkIcon />}
                onClick={() => navigate('/network-analysis', { 
                  state: { accountId: fraudDetails.account_number } 
                })}
              >
                View Network Analysis
              </Button>
            </Box>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ErrorIcon color="error" sx={{ mr: 1 }} />
              <Typography variant="h6">
                Fraud Analysis Results
              </Typography>
            </Box>
            <Chip
              label={`${detectedScenarios.length} Pattern${detectedScenarios.length !== 1 ? 's' : ''} Detected`}
              color="error"
              size="small"
            />
          </Box>

          <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
            Account: {fraudDetails.account_number}
          </Typography>

          <Divider sx={{ mb: 3 }} />

          <Typography variant="h6" sx={{ mb: 2 }}>
            Detected Fraud Patterns:
          </Typography>

          <List>
            {detectedScenarios.map(([scenarioKey, scenario], index) => (
              <ListItem key={scenarioKey} sx={{ pl: 0 }}>
                <ListItemIcon>
                  <WarningIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                      {scenarioKey.replace('_', ' ').toUpperCase()}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary">
                      {scenario.description}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
            <Typography variant="body2" color="error.contrastText">
              <strong>Recommendation:</strong> This account requires immediate investigation.
              Please review the transaction history and consider escalating to the fraud investigation team.
            </Typography>
          </Box>

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<NetworkIcon />}
              onClick={() => navigate('/network-analysis', { 
                state: { accountId: fraudDetails.account_number } 
              })}
            >
              View Network Analysis
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Fraud Detection Dashboard
      </Typography>

      {/* Cache Status Indicator */}
      {cacheInfo && (
        <Alert 
          severity="info" 
          sx={{ mb: 2 }}
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" color="inherit" onClick={findSuspiciousAccounts}>
                Refresh
              </Button>
              <Button size="small" color="inherit" onClick={clearCache}>
                Clear Cache
              </Button>
            </Box>
          }
        >
          <Typography variant="body2">
            <strong>Cached Data:</strong> Showing {cacheInfo.count} accounts from {cacheInfo.timestamp.toLocaleString()} 
            ({cacheInfo.age < 1 ? `${Math.round(cacheInfo.age * 60)}m` : `${cacheInfo.age.toFixed(1)}h`} ago)
          </Typography>
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="contained"
          onClick={findSuspiciousAccounts}
          disabled={loading}
        >
          {loading ? 'Scanning...' : cacheInfo ? 'Refresh Analysis' : 'Find Suspicious Accounts'}
        </Button>
        
        {cacheInfo && (
          <Button
            variant="outlined"
            onClick={clearCache}
            disabled={loading}
          >
            Clear Cache
          </Button>
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {suspiciousAccounts.length > 0 ? (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Suspicious Accounts Detected
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Click on any account number to run detailed fraud pattern analysis
            </Typography>
            <Grid container spacing={1}>
              {suspiciousAccounts.map((account) => (
                <Grid item key={account}>
                  <Button
                    variant="outlined"
                    color="warning"
                    onClick={() => handleAccountClick(account)}
                    disabled={loading}
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.875rem'
                    }}
                  >
                    {account}
                  </Button>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ) : (
        !loading && suspiciousAccounts.length === 0 && (
          <Typography variant="body1" color="text.secondary">
            No suspicious accounts found. Click "Find Suspicious Accounts" to scan the database.
          </Typography>
        )
      )}

      {renderFraudDetails()}
    </Box>
  );
}

export default Dashboard; 