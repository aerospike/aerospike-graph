import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Badge,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  CompareArrows as TransactionsIcon,
  AccountTree as NetworkIcon,
  Description as CasesIcon,
  Warning as AlertsIcon,
  Security as SecurityIcon, // Changed back to Security for a more professional fraud detection look
  Verified as VerifiedIcon, // Added for layered icon effect
} from '@mui/icons-material';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Transactions', icon: <TransactionsIcon />, path: '/transactions' },
  { text: 'Network Analysis', icon: <NetworkIcon />, path: '/network-analysis' },
  { text: 'Cases', icon: <CasesIcon />, path: '/cases' },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box 
            sx={{ 
              position: 'relative',
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 50%, #45B7D1 100%)',
              borderRadius: '12px',
              boxShadow: '0 8px 16px rgba(0,0,0,0.15), 0 0 0 2px rgba(255,255,255,0.1)',
              transform: 'rotate(-3deg)',
              '&:hover': {
                transform: 'rotate(0deg) scale(1.05)',
                transition: 'all 0.3s ease',
                boxShadow: '0 12px 24px rgba(0,0,0,0.2)',
              }
            }}
          >
            <SecurityIcon 
              sx={{ 
                width: 24, 
                height: 24, 
                color: 'white',
                filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                zIndex: 2,
              }} 
            />
            <VerifiedIcon
              sx={{
                position: 'absolute',
                width: 12,
                height: 12,
                color: '#FFD700',
                top: 2,
                right: 2,
                filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.5))',
                zIndex: 3,
              }}
            />
          </Box>
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 'bold',
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '0.5px'
              }}
            >
              FraudGuard
            </Typography>
          </Box>
        </Typography>
        <Box sx={{ mt: 1, ml: 5.5 }}>
          <Typography 
            variant="subtitle2" 
            sx={{ 
              color: 'primary.main',
              fontWeight: 'medium',
              fontSize: '0.8rem'
            }}
          >
            Advanced Fraud Detection
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              color: 'text.secondary',
              display: 'block',
              fontSize: '0.7rem',
              mt: 0.25,
              fontStyle: 'italic'
            }}
          >
            Powered by Aerospike Graph
          </Typography>
        </Box>
      </Box>
      
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            selected={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            sx={{
              mb: 0.5,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'white',
                },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              {item.badge ? (
                <Badge badgeContent={item.badge} color="error">
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            <ListItemText 
              primary={item.text}
              secondary={item.subtitle}
              primaryTypographyProps={{
                variant: 'body2',
                fontWeight: location.pathname === item.path ? 'bold' : 'normal',
              }}
              secondaryTypographyProps={{
                variant: 'caption',
              }}
            />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}

export default Sidebar; 