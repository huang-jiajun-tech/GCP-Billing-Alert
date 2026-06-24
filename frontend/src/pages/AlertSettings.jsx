import React, { useState, useEffect } from 'react';
import { Table, Typography, Button, Modal, Form, Input, InputNumber, Switch, message, Space, Popconfirm, Select, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined, PlayCircleOutlined } from '@ant-design/icons';
import api from '../api';

const { Title, Text } = Typography;
const { Option } = Select;

const AlertSettings = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [triggeringCheck, setTriggeringCheck] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/alerts');
      setConfigs(response.data);
    } catch (error) {
      message.error('Failed to fetch alert configs');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingConfig(null);
    form.resetFields();
    form.setFieldsValue({ 
      is_active: true, 
      threshold: 100, 
      project_ids: [], 
      time_range_days: 1, 
      service_description: '',
      alert_type: 'absolute',
      comparison_window: 'week',
      threshold_percentage: 50
    });
    setIsModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingConfig(record);
    form.setFieldsValue({
      ...record,
      project_ids: record.project_ids || [],
      threshold_percentage: record.threshold_percentage ? record.threshold_percentage * 100 : 50
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (configId) => {
    try {
      await api.delete(`/alerts/${configId}`);
      message.success('Deleted successfully');
      fetchConfigs();
    } catch (error) {
      message.error('Failed to delete');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      // If project_ids is empty array, send null to indicate "All Projects"
      const payload = {
        ...values,
        project_ids: values.project_ids && values.project_ids.length > 0 ? values.project_ids : null,
        threshold_percentage: values.alert_type === 'relative' && values.threshold_percentage ? values.threshold_percentage / 100 : null,
        comparison_window: values.alert_type === 'relative' ? values.comparison_window : null,
        threshold: values.alert_type === 'absolute' ? values.threshold : 0
      };

      if (editingConfig) {
        await api.put(`/alerts/${editingConfig.id}`, payload);
        message.success('Updated successfully');
      } else {
        await api.post('/alerts', payload);
        message.success('Created successfully');
      }
      setIsModalVisible(false);
      fetchConfigs();
    } catch (error) {
      if (error.response && error.response.data) {
        message.error(error.response.data.detail || 'Operation failed');
      } else if (!error.errorFields) {
        message.error('Operation failed');
      }
    }
  };

  const handleToggleActive = async (checked, record) => {
    try {
      await api.put(`/alerts/${record.id}`, { ...record, is_active: checked });
      message.success(`${checked ? 'Enabled' : 'Disabled'} successfully`);
      fetchConfigs();
    } catch (error) {
      message.error('Operation failed');
    }
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields(['webhook_url', 'email']);
      if (!values.webhook_url && !values.email) {
        message.warning('Please provide at least a Webhook URL or Email to test.');
        return;
      }
      
      setTestingConnection(true);
      const response = await api.post('/alerts/test', {
        webhook_url: values.webhook_url,
        email: values.email
      });
      
      message.success(response.data.message || 'Test successful!');
    } catch (error) {
      if (error.response && error.response.data) {
        message.error(error.response.data.detail || 'Test failed');
      } else if (!error.errorFields) {
        message.error('Test failed to execute');
      }
    } finally {
      setTestingConnection(false);
    }
  };

  const handleTriggerCheck = async () => {
    try {
      setTriggeringCheck(true);
      await api.post('/alerts/trigger-check');
      message.success('Alert check job triggered successfully. Please check your notifications or Alert Incidents page shortly.');
    } catch (error) {
      message.error('Failed to trigger alert check');
    } finally {
      setTriggeringCheck(false);
    }
  };

  const columns = [
    {
      title: 'Alert Name',
      dataIndex: 'alert_name',
      key: 'alert_name',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Target Projects',
      dataIndex: 'project_ids',
      key: 'project_ids',
      render: (projectIds) => {
        if (!projectIds || projectIds.length === 0) {
          return <Tag color="blue">All Projects</Tag>;
        }
        return (
          <Space wrap>
            {projectIds.map(pid => <Tag key={pid}>{pid}</Tag>)}
          </Space>
        );
      }
    },
    {
      title: 'Service',
      dataIndex: 'service_description',
      key: 'service_description',
      render: (val) => val ? <Tag color="purple">{val}</Tag> : <Tag>All Services</Tag>,
    },
    {
      title: 'Alert Type',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (val) => val === 'relative' ? <Tag color="orange">Relative (环比)</Tag> : <Tag color="cyan">Absolute (绝对值)</Tag>,
    },
    {
      title: 'Time Range',
      dataIndex: 'time_range_days',
      key: 'time_range_days',
      render: (val) => `${val} Day(s)`,
    },
    {
      title: 'Threshold',
      key: 'threshold_display',
      render: (_, record) => {
        if (record.alert_type === 'relative') {
          const windowText = record.comparison_window === 'week' ? 'Last Week' : 'Last Month';
          const pct = record.threshold_percentage ? (record.threshold_percentage * 100).toFixed(0) : 0;
          return <Text type="warning">+{pct}% vs {windowText}</Text>;
        }
        return <Text>${record.threshold} USD</Text>;
      }
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (val) => val || '-',
    },
    {
      title: 'Webhook',
      dataIndex: 'webhook_url',
      key: 'webhook_url',
      render: (val) => val ? <Text type="success">Configured</Text> : '-',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive, record) => (
        <Switch 
          checked={isActive} 
          onChange={(checked) => handleToggleActive(checked, record)} 
          size="small"
        />
      ),
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button type="text" style={{ color: '#1a73e8' }} icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm
            title="Are you sure to delete this config?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: '1200px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid #dadce0', paddingBottom: 16 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 400 }}>Alert Settings</Title>
        <Space>
          <Button 
            icon={<PlayCircleOutlined />} 
            onClick={handleTriggerCheck} 
            loading={triggeringCheck}
            style={{ borderRadius: 4 }}
          >
            Run Check Now
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} style={{ borderRadius: 4 }}>
            Create Alert
          </Button>
        </Space>
      </div>

      <div style={{ border: '1px solid #dadce0', borderRadius: 8, overflow: 'hidden' }}>
        <Table 
          dataSource={configs} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          size="middle"
        />
      </div>

      <Modal
        title={editingConfig ? "Edit Alert Configuration" : "Create Alert Configuration"}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        destroyOnClose
        okText="Save"
        cancelText="Cancel"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="alert_name"
            label="Alert Name"
            rules={[{ required: true, message: 'Please enter Alert Name' }]}
          >
            <Input placeholder="e.g. High Cost Alert" />
          </Form.Item>

          <Form.Item
            name="project_ids"
            label="Target Projects (Leave empty for All Projects)"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Type project IDs and press enter"
              tokenSeparators={[',']}
            >
            </Select>
          </Form.Item>
          
          <Form.Item
            name="service_description"
            label="Service Description (Optional)"
          >
            <Input placeholder="e.g. Vertex AI (Leave empty for all services)" />
          </Form.Item>
          
          <Form.Item
            name="time_range_days"
            label="Time Range"
            rules={[{ required: true, message: 'Please select time range' }]}
          >
            <Select>
              <Option value={1}>Last 1 Day</Option>
              <Option value={3}>Last 3 Days</Option>
              <Option value={7}>Last 7 Days</Option>
              <Option value={14}>Last 14 Days</Option>
              <Option value={30}>Last 30 Days</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="alert_type"
            label="Alert Type"
            rules={[{ required: true, message: 'Please select alert type' }]}
          >
            <Select>
              <Option value="absolute">Absolute Threshold (绝对值告警)</Option>
              <Option value="relative">Relative Growth (环比告警)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.alert_type !== currentValues.alert_type}
          >
            {({ getFieldValue }) => 
              getFieldValue('alert_type') === 'absolute' ? (
                <Form.Item
                  name="threshold"
                  label="Cost Threshold per Project (USD)"
                  rules={[{ required: true, message: 'Please enter threshold' }]}
                >
                  <InputNumber min={0} step={10} style={{ width: '100%' }} />
                </Form.Item>
              ) : (
                <>
                  <Form.Item
                    name="comparison_window"
                    label="Comparison Window"
                    rules={[{ required: true, message: 'Please select comparison window' }]}
                  >
                    <Select>
                      <Option value="week">vs Same Day Last Week (同比上周)</Option>
                      <Option value="month">vs Same Day Last Month (同比上月)</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name="threshold_percentage"
                    label="Growth Threshold (%)"
                    rules={[{ required: true, message: 'Please enter growth threshold percentage' }]}
                  >
                    <InputNumber 
                      min={0} 
                      step={5} 
                      formatter={value => `${value}%`}
                      parser={value => value.replace('%', '')}
                      style={{ width: '100%' }} 
                      placeholder="e.g. 50 for 50% growth"
                    />
                  </Form.Item>
                </>
              )
            }
          </Form.Item>
          
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', marginBottom: 24 }}>
            <div style={{ flex: 1 }}>
              <Form.Item
                name="email"
                label="Notification Email"
                rules={[{ type: 'email', message: 'Please enter a valid email' }]}
                style={{ marginBottom: 0 }}
              >
                <Input placeholder="e.g. admin@example.com" />
              </Form.Item>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', marginBottom: 24 }}>
            <div style={{ flex: 1 }}>
              <Form.Item
                name="webhook_url"
                label="Webhook URL (WeChat/DingTalk/Lark)"
                style={{ marginBottom: 0 }}
              >
                <Input placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
              </Form.Item>
            </div>
            <Button 
              icon={<ApiOutlined />} 
              onClick={handleTestConnection} 
              loading={testingConnection}
            >
              Test Connection
            </Button>
          </div>
          
          <Form.Item
            name="is_active"
            label="Active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertSettings;
