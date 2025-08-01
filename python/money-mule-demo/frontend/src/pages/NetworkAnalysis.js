import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Card,
  CardContent,
  Chip,
  Grid,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemText,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  AccountTree as NetworkIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';

// Use a simpler, more reliable network visualization
import { Network } from '@visx/network';

const API_BASE_URL = 'http://localhost:5000/api';

// Simple Network Visualization Component
const SimpleNetworkGraph = ({ data, onNodeClick, width = 800, height = 600 }) => {
  const nodes = data.nodes || [];
  const links = data.links || [];

  // Create a simple layout - position nodes in a circle around the main account
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;

  const layoutNodes = nodes.map((node, index) => {
    if (node.type === 'main_account') {
      return { ...node, x: centerX, y: centerY };
    } else {
      const angle = (index / (nodes.length - 1)) * 2 * Math.PI;
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    }
  });

  return (
    <svg width={width} height={height} style={{ border: '1px solid #e0e0e0', borderRadius: '4px' }}>
      {/* Draw links */}
      {links.map((link, index) => {
        const sourceNode = layoutNodes.find(n => n.id === link.source);
        const targetNode = layoutNodes.find(n => n.id === link.target);
        
        if (!sourceNode || !targetNode) return null;

        return (
          <g key={index}>
            <line
              x1={sourceNode.x}
              y1={sourceNode.y}
              x2={targetNode.x}
              y2={targetNode.y}
              stroke={link.color || '#999'}
              strokeWidth={2}
              markerEnd="url(#arrowhead)"
            />
          </g>
        );
      })}

      {/* Arrow marker definition */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill="#666"
          />
        </marker>
      </defs>

      {/* Draw nodes */}
      {layoutNodes.map((node, index) => (
        <g key={index}>
          <circle
            cx={node.x}
            cy={node.y}
            r={node.size || 10}
            fill={node.color || '#45b7d1'}
            stroke="#fff"
            strokeWidth="2"
            style={{ cursor: 'pointer' }}
            onClick={() => onNodeClick && onNodeClick(node)}
          />
          <text
            x={node.x}
            y={node.y + (node.size || 10) + 15}
            textAnchor="middle"
            fontSize="12"
            fill="#333"
            style={{ cursor: 'pointer' }}
            onClick={() => onNodeClick && onNodeClick(node)}
          >
            {node.name.length > 15 ? node.name.substring(0, 15) + '...' : node.name}
          </text>
        </g>
      ))}
    </svg>
  );
};

function NetworkAnalysis() {
  const location = useLocation();
  const [accountId, setAccountId] = useState('');
  const [networkData, setNetworkData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [detailedNodeData, setDetailedNodeData] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState(null);
  const graphRef = useRef();

  // Add debug logging
  console.log('NetworkAnalysis component rendered');
  console.log('Location state:', location.state);

  // Load account from navigation state if available
  useEffect(() => {
    if (location.state?.accountId) {
      setAccountId(location.state.accountId);
      // Auto-load the network for the passed account
      setTimeout(() => {
        loadNetworkDataForAccount(location.state.accountId);
      }, 100);
    }
  }, [location.state]);

  const loadNetworkDataForAccount = async (targetAccountId) => {
    if (!targetAccountId?.trim()) {
      setError('Please enter an account ID');
      return;
    }

    try {
      setError(null);
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/network/${targetAccountId.trim()}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load network data');
      }
      
      const data = await response.json();
      console.log('Network data received:', data);
      setNetworkData(data);
      setSelectedNode(null);
      setDetailedNodeData(null);
      setSidebarOpen(false);
    } catch (err) {
      setError(err.message);
      setNetworkData(null);
    } finally {
      setLoading(false);
    }
  };

  const loadNetworkData = () => {
    loadNetworkDataForAccount(accountId);
  };

  const fetchAccountDetails = async (accountId) => {
    try {
      setLoadingDetails(true);
      console.log('Fetching detailed data for account:', accountId);
      
      const response = await fetch(`${API_BASE_URL}/account-details/${accountId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load account details');
      }
      
      const detailData = await response.json();
      console.log('Detailed account data received:', detailData);
      setDetailedNodeData(detailData);
    } catch (err) {
      console.error('Error fetching account details:', err);
      setDetailedNodeData({ error: err.message });
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleNodeClick = useCallback((node) => {
    console.log('Node clicked:', node);
    setSelectedNode(node);
    setSidebarOpen(true);
    
    // Fetch detailed data for any node (main or connected)
    fetchAccountDetails(node.id);
    
    // This part of the logic needs to be adapted for the new visualization
    // as the graph is now rendered in an SVG.
    // For now, we'll just set the selected node.
  }, []);

  const handleNodeHover = useCallback((node) => {
    // This functionality needs to be re-evaluated for the new visualization
    // as there's no ForceGraph2D instance to interact with.
    // For now, it will be removed or replaced.
  }, []);

  const getNodeColor = (node) => {
    if (node.type === 'main_account') return '#ff4444';
    return node.color || '#45b7d1';
  };

  const getLinkColor = (link) => {
    return link.color || '#999999';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const formatDateTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString();
  };

  const renderNodeTooltip = (node) => {
    return `
      <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px;">
        <strong>${node.name}</strong><br/>
        Bank: ${node.bank}<br/>
        Type: ${node.account_type}<br/>
        ${node.transaction_volume ? `Volume: ${formatCurrency(node.transaction_volume)}` : ''}
      </div>
    `;
  };

  const renderLinkTooltip = (link) => {
    return `
      <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px;">
        <strong>Transaction</strong><br/>
        Amount: ${formatCurrency(link.amount)}<br/>
        Type: ${link.type}<br/>
        ID: ${link.transaction_id}<br/>
        Date: ${formatDateTime(link.datetime)}
      </div>
    `;
  };

  const getConnectedTransactions = (nodeId) => {
    if (!networkData) return [];
    
    console.log('Getting transactions for node:', nodeId);
    console.log('Available links:', networkData.links);
    
    // Fix the filtering logic - compare with string IDs
    const transactions = networkData.links.filter(
      link => {
        const sourceMatch = String(link.source) === String(nodeId);
        const targetMatch = String(link.target) === String(nodeId);
        console.log(`Link ${link.source} -> ${link.target}: sourceMatch=${sourceMatch}, targetMatch=${targetMatch}`);
        return sourceMatch || targetMatch;
      }
    );
    
    console.log(`Found ${transactions.length} transactions for node ${nodeId}:`, transactions);
    return transactions;
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
          <NetworkIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
          Network Analysis
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          Visualize transaction patterns and account relationships
        </Typography>
        
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Account ID"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && loadNetworkData()}
              placeholder="Enter account ID to analyze"
              variant="outlined"
              size="small"
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <Button
              variant="contained"
              onClick={loadNetworkData}
              disabled={loading}
              fullWidth
              sx={{ height: '40px' }}
            >
              {loading ? <CircularProgress size={20} /> : 'Analyze Network'}
            </Button>
          </Grid>
          {networkData && (
            <Grid item xs={12} md={3}>
              <Chip
                icon={<NetworkIcon />}
                label={`${networkData.total_transactions} Transactions`}
                color="primary"
                variant="outlined"
              />
            </Grid>
          )}
        </Grid>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Network Visualization - Re-enabled! */}
      {networkData && (
        <Paper sx={{ flexGrow: 1, p: 1, position: 'relative' }}>
          <SimpleNetworkGraph
            data={networkData}
            onNodeClick={handleNodeClick}
            width={window.innerWidth - 100}
            height={window.innerHeight - 200}
          />
        </Paper>
      )}

      {/* No Data State */}
      {!networkData && !loading && (
        <Card sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <NetworkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Enter an account ID to visualize its transaction network
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Try using one of the suspicious account IDs from the Dashboard
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Node Details Sidebar */}
      <Drawer
        anchor="right"
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 500,
            height: '100vh', // Full viewport height
            overflow: 'hidden', // Prevent double scrollbars
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        {/* Fixed Header */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          p: 2, 
          borderBottom: '1px solid #e0e0e0',
          flexShrink: 0 // Prevent header from shrinking
        }}>
          <Typography variant="h6">Account Details</Typography>
          <IconButton onClick={() => setSidebarOpen(false)}>
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Scrollable Content Area */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f1f1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#c1c1c1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#a8a8a8',
          },
        }}>
          {selectedNode && (
            <>
              {/* Loading State */}
              {loadingDetails && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" sx={{ ml: 2 }}>
                    Loading account details...
                  </Typography>
                </Box>
              )}

              {/* Main Account Info Card */}
              <Card sx={{ mb: 1.5 }}>
                <CardContent sx={{ pb: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                    <NetworkIcon sx={{ mr: 1, color: selectedNode.type === 'main_account' ? 'error.main' : 'primary.main' }} />
                    <Typography variant="h6" component="div">
                      {selectedNode.name}
                    </Typography>
                  </Box>
                  
                  <Chip
                    label={selectedNode.type === 'main_account' ? 'Main Account (Under Investigation)' : 'Connected Account'}
                    color={selectedNode.type === 'main_account' ? 'error' : 'primary'}
                    size="small"
                    sx={{ mb: 1.5 }}
                  />

                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Account Properties:
                  </Typography>
                  
                  <Grid container spacing={1}>
                    {detailedNodeData && detailedNodeData.properties ? (
                      Object.entries(detailedNodeData.properties).map(([key, value]) => {
                        if (value === null || value === undefined) return null;

                        let displayValue = value;
                        let displayKey = key;

                        switch (key) {
                          case 'vertex_id':
                            displayKey = 'Vertex ID';
                            break;
                          case 'vertex_label':
                            displayKey = 'Vertex Type';
                            break;
                          case 'account_number':
                            displayKey = 'Account Number';
                            break;
                          case 'bank_name':
                            displayKey = 'Bank Name';
                            break;
                          case 'account_type':
                            displayKey = 'Account Type';
                            break;
                          case 'balance':
                            displayKey = 'Current Balance';
                            displayValue = formatCurrency(value);
                            break;
                          case 'open_date':
                            displayKey = 'Open Date';
                            displayValue = new Date(value).toLocaleDateString();
                            break;
                          case 'fraud_block':
                            displayKey = 'Fraud Block Status';
                            displayValue = value ? 'BLOCKED' : 'Active';
                            break;
                          case 'status':
                            displayKey = 'Account Status';
                            displayValue = String(value).toUpperCase();
                            break;
                          case 'currency':
                            displayKey = 'Currency';
                            break;
                          case 'bank_code':
                            displayKey = 'Bank Code';
                            break;
                          default:
                            displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        }

                        return (
                          <Grid item xs={12} key={key}>
                            <Box sx={{ py: 0.5, borderBottom: '1px solid #f0f0f0' }}>
                              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'medium' }}>
                                {displayKey}
                              </Typography>
                              <Typography variant="body1" sx={{ mt: 0.25 }}>
                                {String(displayValue)}
                              </Typography>
                            </Box>
                          </Grid>
                        );
                      })
                    ) : (
                      Object.entries(selectedNode).map(([key, value]) => {
                        if (['x', 'y', '__indexColor', '__threeObj'].includes(key) || value === null || value === undefined) {
                          return null;
                        }

                        let displayValue = value;
                        let displayKey = key;

                        switch (key) {
                          case 'id':
                            displayKey = 'Account ID';
                            break;
                          case 'name':
                            displayKey = 'Display Name';
                            break;
                          case 'type':
                            displayKey = 'Account Type';
                            break;
                          case 'bank':
                            displayKey = 'Bank Name';
                            break;
                          case 'account_type':
                            displayKey = 'Account Category';
                            break;
                          case 'size':
                            displayKey = 'Node Size';
                            break;
                          case 'color':
                            displayKey = 'Display Color';
                            displayValue = (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Box 
                                  sx={{ 
                                    width: 20, 
                                    height: 20, 
                                    backgroundColor: value, 
                                    borderRadius: '50%',
                                    mr: 1,
                                    border: '1px solid #ccc'
                                  }} 
                                />
                                {value}
                              </Box>
                            );
                            break;
                          default:
                            displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        }

                        return (
                          <Grid item xs={12} key={key}>
                            <Box sx={{ py: 0.5, borderBottom: '1px solid #f0f0f0' }}>
                              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'medium' }}>
                                {displayKey}
                              </Typography>
                              <Typography variant="body1" sx={{ mt: 0.25 }}>
                                {typeof displayValue === 'object' ? displayValue : String(displayValue)}
                              </Typography>
                            </Box>
                          </Grid>
                        );
                      })
                    )}
                  </Grid>

                  {detailedNodeData && detailedNodeData.transaction_statistics && (
                    <Box sx={{ mt: 1.5, p: 1.5, bgcolor: 'info.light', borderRadius: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                        Complete Transaction Statistics:
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Total Transactions
                          </Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {detailedNodeData.transaction_statistics.total_transactions}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Unique Connections
                          </Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {detailedNodeData.connection_statistics?.total_unique_connections || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Est. Outgoing Volume
                          </Typography>
                          <Typography variant="body2" color="error.main">
                            {formatCurrency(detailedNodeData.transaction_statistics.estimated_outgoing_volume)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Est. Incoming Volume
                          </Typography>
                          <Typography variant="body2" color="success.main">
                            {formatCurrency(detailedNodeData.transaction_statistics.estimated_incoming_volume)}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </CardContent>
              </Card>

              <Divider sx={{ mb: 2 }} />

              {/* Transaction Analysis */}
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
                    Transaction Analysis
                  </Typography>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
                        <Typography variant="h6" color="error.contrastText">
                          {getConnectedTransactions(selectedNode.id).filter(t => String(t.source) === String(selectedNode.id)).length}
                        </Typography>
                        <Typography variant="caption" color="error.contrastText">
                          Outgoing
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
                        <Typography variant="h6" color="success.contrastText">
                          {getConnectedTransactions(selectedNode.id).filter(t => String(t.target) === String(selectedNode.id)).length}
                        </Typography>
                        <Typography variant="caption" color="success.contrastText">
                          Incoming
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  {(() => {
                    const transactions = getConnectedTransactions(selectedNode.id);
                    const outgoingTotal = transactions
                      .filter(t => String(t.source) === String(selectedNode.id))
                      .reduce((sum, t) => sum + (Number(t.amount) || 0), 0);
                    const incomingTotal = transactions
                      .filter(t => String(t.target) === String(selectedNode.id))
                      .reduce((sum, t) => sum + (Number(t.amount) || 0), 0);

                    return (
                      <Grid container spacing={2} sx={{ mb: 2 }}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Total Outgoing
                          </Typography>
                          <Typography variant="h6" color="error.main">
                            {formatCurrency(outgoingTotal)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Total Incoming
                          </Typography>
                          <Typography variant="h6" color="success.main">
                            {formatCurrency(incomingTotal)}
                          </Typography>
                        </Grid>
                      </Grid>
                    );
                  })()}

                  {(() => {
                    const transactions = getConnectedTransactions(selectedNode.id);
                    const outgoingTotal = transactions
                      .filter(t => String(t.source) === String(selectedNode.id))
                      .reduce((sum, t) => sum + (Number(t.amount) || 0), 0);
                    const incomingTotal = transactions
                      .filter(t => String(t.target) === String(selectedNode.id))
                      .reduce((sum, t) => sum + (Number(t.amount) || 0), 0);
                    const netFlow = incomingTotal - outgoingTotal;

                    return (
                      <Box sx={{ p: 2, bgcolor: netFlow >= 0 ? 'success.light' : 'warning.light', borderRadius: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Net Money Flow
                        </Typography>
                        <Typography variant="h6" color={netFlow >= 0 ? 'success.main' : 'warning.main'}>
                          {netFlow >= 0 ? '+' : ''}{formatCurrency(netFlow)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {netFlow >= 0 ? 'Money accumulator' : 'Money distributor'}
                        </Typography>
                      </Box>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* Connected Transactions List */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Connected Transactions ({getConnectedTransactions(selectedNode.id).length})
                  </Typography>

                  <List dense sx={{ maxHeight: 500, overflow: 'auto' }}>
                    {getConnectedTransactions(selectedNode.id).map((transaction, index) => {
                      const isOutgoing = String(transaction.source) === String(selectedNode.id);
                      const otherAccountId = isOutgoing ? transaction.target : transaction.source;
                      const otherAccount = networkData.nodes.find(n => n.id === otherAccountId);
                      
                      return (
                        <ListItem 
                          key={index} 
                          sx={{ 
                            px: 0, 
                            py: 1,
                            borderBottom: '1px solid #f0f0f0',
                            '&:hover': { bgcolor: 'grey.50' }
                          }}
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Typography variant="body2" fontWeight="medium" sx={{ mr: 1 }}>
                                    {isOutgoing ? '→' : '←'}
                                  </Typography>
                                  <Typography variant="body2" fontWeight="medium">
                                    {formatCurrency(Number(transaction.amount) || 0)}
                                  </Typography>
                                </Box>
                                <Chip
                                  label={transaction.type}
                                  size="small"
                                  color={isOutgoing ? 'error' : 'success'}
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={
                              <>
                                <Typography variant="caption" display="block">
                                  {isOutgoing ? 'To: ' : 'From: '}{otherAccount?.name || otherAccountId}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {formatDateTime(transaction.datetime)} • ID: {transaction.transaction_id}
                                </Typography>
                                <Box sx={{ mt: 1 }}>
                                  {Object.entries(transaction).map(([key, value]) => {
                                    if (['source', 'target', 'amount', 'datetime', 'transaction_id', 'type'].includes(key)) {
                                      return null;
                                    }
                                    return (
                                      <Typography key={key} variant="caption" display="block" color="text.secondary">
                                        {key}: {String(value)}
                                      </Typography>
                                    );
                                  })}
                                </Box>
                              </>
                            }
                          />
                        </ListItem>
                      );
                    })}
                  </List>
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      </Drawer>
    </Box>
  );
}

export default NetworkAnalysis; 