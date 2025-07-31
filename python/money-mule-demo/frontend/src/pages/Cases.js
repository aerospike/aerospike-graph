import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  Select,
  MenuItem,
  InputAdornment,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const API_BASE_URL = 'http://localhost:5000/api';

function Cases() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/cases`);
      if (!response.ok) {
        throw new Error('Failed to fetch cases');
      }
      const data = await response.json();
      setCases(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching cases:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status) => {
    const statusProps = {
      investigating: { color: 'info', label: 'Investigating' },
      open: { color: 'warning', label: 'Open' },
      closed: { color: 'success', label: 'Closed' },
    };
    const { color, label } = statusProps[status] || { color: 'default', label: status };
    return <Chip size="small" color={color} label={label} />;
  };

  const getSeverityChip = (severity) => {
    const severityProps = {
      high: { color: 'warning', label: 'High' },
      critical: { color: 'error', label: 'Critical' },
      medium: { color: 'info', label: 'Medium' },
      low: { color: 'success', label: 'Low' },
    };
    const { color, label } = severityProps[severity] || { color: 'default', label: severity };
    return <Chip size="small" color={color} label={label} />;
  };

  const filteredCases = cases.filter(case_ => {
    const matchesSearch = 
      case_.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      case_.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      case_.id.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || case_.status === statusFilter;
    const matchesSeverity = severityFilter === 'all' || case_.severity === severityFilter;
    
    return matchesSearch && matchesStatus && matchesSeverity;
  });

  const handleClearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setSeverityFilter('all');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Fraud Cases
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ borderRadius: 2 }}
        >
          New Case
        </Button>
      </Box>

      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Manage and track fraud investigation cases
      </Typography>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Search & Filter
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              placeholder="Search cases..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={6} sm={3} md={2}>
            <Select
              fullWidth
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              displayEmpty
            >
              <MenuItem value="all">All Statuses</MenuItem>
              <MenuItem value="open">Open</MenuItem>
              <MenuItem value="investigating">Investigating</MenuItem>
              <MenuItem value="closed">Closed</MenuItem>
            </Select>
          </Grid>
          <Grid item xs={6} sm={3} md={2}>
            <Select
              fullWidth
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              displayEmpty
            >
              <MenuItem value="all">All Severities</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Button 
              variant="outlined" 
              sx={{ mr: 1 }}
              onClick={handleClearFilters}
            >
              Clear Filters
            </Button>
            <Button 
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchCases}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box>
          {filteredCases.length === 0 ? (
            <Alert severity="info">
              No cases found matching your criteria.
            </Alert>
          ) : (
            filteredCases.map((case_) => (
              <Card key={case_.id} sx={{ mb: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" component="div">
                        {case_.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {case_.id}
                      </Typography>
                    </Box>
                    <Box>
                      {getStatusChip(case_.status)}
                      {' '}
                      {getSeverityChip(case_.severity)}
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {case_.description}
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Priority
                      </Typography>
                      <Typography variant="body2">
                        {case_.priority}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Assigned To
                      </Typography>
                      <Typography variant="body2">
                        {case_.assignedTo}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Created
                      </Typography>
                      <Typography variant="body2">
                        {case_.created}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Related Transactions
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {case_.relatedTransactions.map((tx) => (
                        <Chip
                          key={tx}
                          label={tx}
                          size="small"
                          sx={{ mr: 1 }}
                          onClick={() => {}}
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </Box>
      )}
    </Box>
  );
}

export default Cases; 