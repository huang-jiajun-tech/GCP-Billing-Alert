import React, { useState, useEffect } from 'react';
import { Table, Typography, Button, Card, message, Space, Modal, Form, Input, Tag, Tabs, Popconfirm } from 'antd';
import { CheckCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

const AlertIncidents = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [handlingIncident, setHandlingIncident] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [deleting, setDeleting] = useState(false);
  const [form] = Form.useForm();
  
  // Check if current user is admin
  const userStr = localStorage.getItem('user');
  const isAdmin = userStr ? JSON.parse(userStr).role === 'admin' : false;

  useEffect(() => {
    fetchIncidents(activeTab);
  }, [activeTab]);

  const fetchIncidents = async (status) => {
    try {
      setLoading(true);
      const response = await api.get('/incidents', { params: { status } });
      setIncidents(response.data);
      setSelectedRowKeys([]); // Clear selection when data changes
    } catch (error) {
      message.error('Failed to fetch alert incidents');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (record) => {
    setHandlingIncident(record);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      await api.post(`/incidents/${handlingIncident.id}/handle`, values);
      message.success('Incident marked as handled');
      setIsModalVisible(false);
      fetchIncidents(activeTab);
    } catch (error) {
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) return;
    
    try {
      setDeleting(true);
      await api.delete('/incidents', {
        data: { incident_ids: selectedRowKeys }
      });
      message.success(`Successfully deleted ${selectedRowKeys.length} incidents`);
      fetchIncidents(activeTab);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete incidents');
    } finally {
      setDeleting(false);
    }
  };

  const onSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };

  const columns = [
    {
      title: 'Alert Time',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val) => dayjs(val).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Project ID',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Cost / Threshold',
      key: 'cost_threshold',
      render: (_, record) => {
        const isRelative = record.config?.alert_type === 'relative';
        return (
          <Space>
            <Text type="danger">${record.cost.toFixed(2)}</Text>
            <Text type="secondary">
              / {isRelative ? `+${(record.threshold * 100).toFixed(0)}%` : `$${record.threshold.toFixed(2)}`}
            </Text>
          </Space>
        );
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'handled' ? 'success' : 'warning'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
  ];

  if (activeTab === 'handled') {
    columns.push(
      {
        title: 'Handled At',
        dataIndex: 'handled_at',
        key: 'handled_at',
        render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm:ss') : '-',
      },
      {
        title: 'Handler',
        key: 'handler',
        render: (_, record) => record.handler?.username || '-',
      },
      {
        title: 'Notes',
        dataIndex: 'handle_notes',
        key: 'handle_notes',
      }
    );
  } else {
    columns.push({
      title: 'Actions',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="primary" 
          size="small" 
          icon={<CheckCircleOutlined />} 
          onClick={() => handleOpenModal(record)}
        >
          Handle
        </Button>
      ),
    });
  }

  return (
    <div style={{ maxWidth: '1200px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid #dadce0', paddingBottom: 16 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 400 }}>Alert Incidents</Title>
        {isAdmin && selectedRowKeys.length > 0 && (
          <Popconfirm
            title={`Are you sure to delete ${selectedRowKeys.length} selected incidents?`}
            onConfirm={handleBatchDelete}
            okText="Yes"
            cancelText="No"
          >
            <Button type="primary" danger icon={<DeleteOutlined />} loading={deleting}>
              Delete Selected ({selectedRowKeys.length})
            </Button>
          </Popconfirm>
        )}
      </div>

      <Card bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8 }}>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            { key: 'pending', label: 'Pending Alerts' },
            { key: 'handled', label: 'Handled History' }
          ]}
        />
        <Table 
          rowSelection={isAdmin ? rowSelection : undefined}
          dataSource={incidents} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      <Modal
        title="Handle Alert Incident"
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        destroyOnClose
        okText="Mark as Handled"
      >
        <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 4 }}>
          <Text strong>Project: </Text> <Text>{handlingIncident?.project_id}</Text><br/>
          <Text strong>Cost: </Text> <Text type="danger">${handlingIncident?.cost}</Text><br/>
          <Text type="secondary" style={{ fontSize: 12 }}>
            * Marking this as handled will suppress new alerts for this project for the next 3 days.
          </Text>
        </div>
        <Form form={form} layout="vertical">
          <Form.Item
            name="handle_notes"
            label="Handling Notes / Resolution"
            rules={[{ required: true, message: 'Please provide handling notes' }]}
          >
            <TextArea rows={4} placeholder="Describe how this alert was resolved..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertIncidents;
