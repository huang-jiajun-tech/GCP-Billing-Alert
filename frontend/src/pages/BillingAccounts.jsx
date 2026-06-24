import React, { useState, useEffect } from 'react';
import { Table, Typography, Button, Card, message, Input, Space } from 'antd';
import { SyncOutlined, SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import api from '../api';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';

const { Title, Text } = Typography;

const BillingAccounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async (search = '') => {
    try {
      setLoading(true);
      const response = await api.get('/billing-accounts', {
        params: { search }
      });
      setAccounts(response.data);
    } catch (error) {
      message.error('Failed to fetch billing accounts');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchAccounts(searchText);
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await api.post('/billing-accounts/sync');
      message.success('Sync triggered successfully');
      // Wait a bit for the sync to complete before fetching again
      setTimeout(() => fetchAccounts(searchText), 2000);
    } catch (error) {
      message.error('Failed to trigger sync');
      console.error(error);
    } finally {
      setSyncing(false);
    }
  };

  const handleExportExcel = () => {
    if (accounts.length === 0) {
      message.warning('No data to export');
      return;
    }

    // Prepare data for Excel
    const exportData = accounts.map(acc => ({
      'Billing Account ID': acc.billing_account_id,
      'Billing Name': acc.display_name,
      'Last Updated': acc.last_updated ? dayjs(acc.last_updated).format('YYYY-MM-DD HH:mm:ss') : '-'
    }));

    // Create worksheet
    const ws = XLSX.utils.json_to_sheet(exportData);
    
    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Billing Accounts");
    
    // Generate Excel file and trigger download
    XLSX.writeFile(wb, `Billing_Accounts_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`);
  };

  const columns = [
    {
      title: 'Billing Account ID',
      dataIndex: 'billing_account_id',
      key: 'billing_account_id',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Billing Name',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: 'Last Updated',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
  ];

  return (
    <div style={{ maxWidth: '1200px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid #dadce0', paddingBottom: 16 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 400 }}>Billing Accounts</Title>
        <Space>
          <Input
            placeholder="Search by ID or Name"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 250 }}
            suffix={<SearchOutlined onClick={handleSearch} style={{ cursor: 'pointer', color: '#1a73e8' }} />}
          />
          <Button 
            type="primary" 
            icon={<SyncOutlined spin={syncing} />} 
            onClick={handleSync} 
            loading={syncing}
            style={{ borderRadius: 4 }}
          >
            Sync from GCP
          </Button>
          <Button 
            icon={<DownloadOutlined />} 
            onClick={handleExportExcel}
            style={{ borderRadius: 4 }}
          >
            Export to Excel
          </Button>
        </Space>
      </div>

      <Card bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8 }}>
        <Table 
          dataSource={accounts} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ 
            defaultPageSize: 15,
            showSizeChanger: true,
            pageSizeOptions: ['15', '30', '50', '100']
          }}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default BillingAccounts;
