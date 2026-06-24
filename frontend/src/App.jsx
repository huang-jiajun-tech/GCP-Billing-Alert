import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { Layout, Menu, Input, Avatar, ConfigProvider, Dropdown } from 'antd';
import { DashboardOutlined, AlertOutlined, SearchOutlined, BellOutlined, QuestionCircleOutlined, AccountBookOutlined, UserOutlined, LogoutOutlined, ExceptionOutlined, CloudSyncOutlined } from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import AlertSettings from './pages/AlertSettings';
import BillingAccounts from './pages/BillingAccounts';
import UserManagement from './pages/UserManagement';
import AlertIncidents from './pages/AlertIncidents';
import DailyUsageSync from './pages/DailyUsageSync';
import Login from './pages/Login';
import 'antd/dist/reset.css';

const { Header, Content, Sider } = Layout;

const AppMenu = ({ user }) => {
  const location = useLocation();
  
  const items = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">Billing Overview</Link>,
    },
    {
      key: '/billing-accounts',
      icon: <AccountBookOutlined />,
      label: <Link to="/billing-accounts">Billing Accounts</Link>,
    },
    {
      key: '/incidents',
      icon: <ExceptionOutlined />,
      label: <Link to="/incidents">Alert Incidents</Link>,
    },
    {
      key: '/alerts',
      icon: <AlertOutlined />,
      label: <Link to="/alerts">Alert Settings</Link>,
    },
  ];

  if (user && user.role === 'admin') {
    items.push({
      key: '/sync',
      icon: <CloudSyncOutlined />,
      label: <Link to="/sync">Daily Usage Sync</Link>,
    });
    items.push({
      key: '/users',
      icon: <UserOutlined />,
      label: <Link to="/users">User Management</Link>,
    });
  }

  return (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={items}
      style={{ borderRight: 0, backgroundColor: 'transparent' }}
    />
  );
};

const ProtectedRoute = ({ children, user, requireAdmin }) => {
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (requireAdmin && user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }
  return children;
};

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) return null;

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Logout',
        onClick: handleLogout,
      },
    ],
  };

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1a73e8',
          borderRadius: 4,
          fontFamily: 'Roboto, Arial, sans-serif',
        },
        components: {
          Menu: {
            itemSelectedBg: '#e8f0fe',
            itemSelectedColor: '#1967d2',
          },
          Layout: {
            headerBg: '#ffffff',
            bodyBg: '#ffffff',
            siderBg: '#ffffff',
          }
        }
      }}
    >
      <Router>
        <Routes>
          <Route path="/login" element={
            user ? <Navigate to="/" replace /> : <Login onLoginSuccess={setUser} />
          } />
          
          <Route path="/*" element={
            <ProtectedRoute user={user}>
              <Layout style={{ minHeight: '100vh' }}>
                <Header style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  padding: '0 24px', 
                  borderBottom: '1px solid #dadce0',
                  height: '64px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ fontSize: '18px', color: '#5f6368', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <img src="/favicon.png" alt="Logo" style={{ height: '32px', width: 'auto', objectFit: 'contain' }} />
                      <span style={{ color: '#5f6368', fontSize: '20px' }}>Billing Alert System</span>
                    </div>
                  </div>
                  
                  <div style={{ flex: 1, maxWidth: '720px', margin: '0 48px' }}>
                    <Input 
                      prefix={<SearchOutlined style={{ color: '#5f6368' }} />} 
                      placeholder="Search resources, docs, products, and more" 
                      style={{ backgroundColor: '#f1f3f4', border: 'none', borderRadius: '8px', padding: '8px 16px' }}
                    />
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', color: '#5f6368', fontSize: '20px' }}>
                    <QuestionCircleOutlined />
                    <BellOutlined />
                    <Dropdown menu={userMenu} placement="bottomRight">
                      <Avatar style={{ backgroundColor: '#1a73e8', cursor: 'pointer' }}>
                        {user?.username?.charAt(0).toUpperCase()}
                      </Avatar>
                    </Dropdown>
                  </div>
                </Header>
                
                <Layout>
                  <Sider width={256} style={{ borderRight: '1px solid #dadce0' }}>
                    {/* <div style={{ padding: '16px 24px', fontSize: '14px', fontWeight: 500, color: '#5f6368', borderBottom: '1px solid #dadce0', marginBottom: '8px' }}>
                      GenAI Alert System
                    </div> */}
                    <AppMenu user={user} />
                  </Sider>
                  <Content style={{ padding: '24px', backgroundColor: '#ffffff' }}>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/billing-accounts" element={<BillingAccounts />} />
                      <Route path="/incidents" element={<AlertIncidents />} />
                      <Route path="/alerts" element={<AlertSettings />} />
                      <Route path="/sync" element={
                        <ProtectedRoute user={user} requireAdmin={true}>
                          <DailyUsageSync />
                        </ProtectedRoute>
                      } />
                      <Route path="/users" element={
                        <ProtectedRoute user={user} requireAdmin={true}>
                          <UserManagement />
                        </ProtectedRoute>
                      } />
                    </Routes>
                  </Content>
                </Layout>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </ConfigProvider>
  );
};

export default App;
