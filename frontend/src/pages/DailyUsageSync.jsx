import React, { useState, useEffect } from 'react';
import { Table, Typography, Button, Card, message, Space, DatePicker, Tag } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import api from '../api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const DailyUsageSync = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [dateRange, setDateRange] = useState([dayjs().subtract(3, 'day'), dayjs()]);

  useEffect(() => {
    fetchLogs();
    // Poll for updates if there are running syncs
    const interval = setInterval(() => {
      fetchLogs(false);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const response = await api.get('/sync/logs');
      setLogs(response.data);
    } catch (error) {
      if (showLoading) message.error('Failed to fetch sync logs');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleManualSync = async () => {
    if (!dateRange || dateRange.length !== 2) {
      message.warning('Please select a date range');
      return;
    }

    try {
      setSyncing(true);
      await api.post('/sync/usage', {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD')
      });
      message.success('Manual sync started in the background');
      fetchLogs();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to start manual sync');
    } finally {
      setSyncing(false);
    }
  };

  const columns = [
    {
      title: 'Sync Type',
      dataIndex: 'sync_type',
      key: 'sync_type',
      render: (type) => (
        <Tag color={type === 'manual' ? 'blue' : 'default'}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Target Date Range',
      key: 'target_dates',
      render: (_, record) => `${record.target_start_date} to ${record.target_end_date}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        let color = 'default';
        if (status === 'success') color = 'success';
        if (status === 'failed') color = 'error';
        if (status === 'running') color = 'processing';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Records Synced',
      dataIndex: 'records_synced',
      key: 'records_synced',
      render: (val) => <Text strong>{val}</Text>,
    },
    {
      title: 'Started At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val) => dayjs(val).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Completed At',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: 'Error Message',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (val) => val ? <Text type="danger" ellipsis={{ tooltip: val }} style={{ maxWidth: 200 }}>{val}</Text> : '-',
    },
  ];

  return (
    <div style={{ maxWidth: '1200px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid #dadce0', paddingBottom: 16 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 400 }}>Daily Usage Sync</Title>
        <Space>
          <RangePicker 
            value={dateRange} 
            onChange={setDateRange} 
            disabledDate={(current) => current && current > dayjs().endOf('day')}
          />
          <Button 
            type="primary" 
            icon={<SyncOutlined spin={syncing} />} 
            onClick={handleManualSync} 
            loading={syncing}
            style={{ borderRadius: 4 }}
          >
            Trigger Manual Sync
          </Button>
        </Space>
      </div>

      <Card bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8 }}>
        <Title level={5} style={{ marginTop: 0, marginBottom: 16 }}>Sync History</Title>
        <Table 
          dataSource={logs} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default DailyUsageSync;
