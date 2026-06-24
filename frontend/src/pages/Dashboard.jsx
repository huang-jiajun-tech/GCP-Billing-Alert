import React, { useState, useEffect } from 'react';
import { Table, Typography, Row, Col, message, DatePicker, Card, Input, Select, Space, Button } from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../api';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Dashboard = () => {
  const [usageData, setUsageData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCost, setTotalCost] = useState(0);
  
  // Filters state
  const [dateRange, setDateRange] = useState([dayjs().subtract(2, 'day'), dayjs().subtract(1, 'day')]);
  const [projectId, setProjectId] = useState('');
  const [billingId, setBillingId] = useState('');
  const [minCost, setMinCost] = useState(0);
  const [serviceDescription, setServiceDescription] = useState('Vertex AI');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const startDate = dateRange[0].format('YYYY-MM-DD');
      const endDate = dateRange[1].format('YYYY-MM-DD');
      
      const params = {
        start_date: startDate,
        end_date: endDate,
        min_cost: minCost
      };
      
      if (projectId) params.project_id = projectId;
      if (billingId) params.billing_account_id = billingId;
      if (serviceDescription) params.service_description = serviceDescription;

      // Fetch aggregated usage data for table and histogram
      const usageResponse = await api.get('/usage', { params });
      setUsageData(usageResponse.data);
      
      const total = usageResponse.data.reduce((sum, item) => sum + item.cost, 0);
      setTotalCost(total);

      // Fetch trend data for line chart
      const trendResponse = await api.get('/usage/trend', { params });
      setTrendData(trendResponse.data);
      
    } catch (error) {
      message.error('Failed to fetch usage data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const generateDateColumns = () => {
    const cols = [];
    let currentDate = dayjs(dateRange[0]);
    const endDate = dayjs(dateRange[1]);

    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate, 'day')) {
      const dateStr = currentDate.format('YYYY-MM-DD');
      cols.push({
        title: currentDate.format('MM-DD'),
        dataIndex: ['daily_costs', dateStr],
        key: dateStr,
        width: 100,
        render: (val) => {
          if (!val) return '$0.00';
          const isExceeding = minCost > 0 && val > minCost;
          return <Text style={{ color: isExceeding ? '#ea4335' : 'inherit', fontWeight: isExceeding ? 'bold' : 'normal' }}>${val.toFixed(2)}</Text>;
        },
        sorter: (a, b) => (a.daily_costs?.[dateStr] || 0) - (b.daily_costs?.[dateStr] || 0),
      });
      currentDate = currentDate.add(1, 'day');
    }
    return cols;
  };

  const handleDownloadExcel = () => {
    if (!usageData || usageData.length === 0) {
      message.warning('No data to export');
      return;
    }

    let currentDate = dayjs(dateRange[0]);
    const endDate = dayjs(dateRange[1]);
    const dateHeaders = [];
    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate, 'day')) {
      dateHeaders.push(currentDate.format('YYYY-MM-DD'));
      currentDate = currentDate.add(1, 'day');
    }

    const excelData = usageData.map(item => {
      const row = {
        'Project ID': item.project_id,
        'Customer': item.customer_name,
        'Sales Rep': item.sales_rep,
        'Billing Account ID': item.billing_account_id,
        'Billing Name': item.billing_name,
      };
      
      dateHeaders.forEach(date => {
        row[date] = item.daily_costs?.[date] || 0;
      });
      
      row['Total Cost'] = item.total_cost || item.cost || 0;
      row['Currency'] = item.currency;
      return row;
    });

    const worksheet = XLSX.utils.json_to_sheet(excelData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Usage Details');
    
    const fileName = `Billing_Usage_${dateRange[0].format('YYYYMMDD')}_to_${dateRange[1].format('YYYYMMDD')}.xlsx`;
    XLSX.writeFile(workbook, fileName);
  };

  const baseColumns = [
    {
      title: 'Project ID',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (text) => <Text strong style={{ color: '#1a73e8' }}>{text}</Text>,
      fixed: 'left',
      width: 180,
    },
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
    },
    {
      title: 'Sales Rep',
      dataIndex: 'sales_rep',
      key: 'sales_rep',
      width: 120,
    },
    {
      title: 'Billing Account ID',
      dataIndex: 'billing_account_id',
      key: 'billing_account_id',
      width: 160,
    },
    {
      title: 'Billing Name',
      dataIndex: 'billing_name',
      key: 'billing_name',
      width: 200,
    }
  ];

  const columns = [
    ...baseColumns,
    ...generateDateColumns(),
    {
      title: 'Total Cost',
      dataIndex: 'total_cost',
      key: 'total_cost',
      render: (cost, record) => `$${(cost || record.cost).toFixed(2)} ${record.currency}`,
      sorter: (a, b) => (a.total_cost || a.cost) - (b.total_cost || b.cost),
      fixed: 'right',
      width: 120,
    },
  ];

  // Process trend data to only show top 10 projects + "Other" to prevent rendering crashes
  const processedTrendData = React.useMemo(() => {
    if (!usageData.length || !trendData.length) return [];
    
    const topProjects = usageData.slice(0, 10).map(item => item.project_id);
    
    return trendData.map(day => {
      const newDay = { date: day.date, cost: day.cost, currency: day.currency };
      let topCost = 0;
      
      topProjects.forEach(pid => {
        if (day[pid]) {
          newDay[pid] = day[pid];
          topCost += day[pid];
        }
      });
      
      const otherCost = day.cost - topCost;
      if (otherCost > 0.01) {
        newDay['Other'] = Number(otherCost.toFixed(2));
      }
      
      return newDay;
    });
  }, [usageData, trendData]);

  const chartProjects = React.useMemo(() => {
    const top = usageData.slice(0, 10).map(item => item.project_id);
    if (usageData.length > 10) {
      return [...top, 'Other'];
    }
    return top;
  }, [usageData]);

  const projectColors = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#46bdc6', '#ff6d01', '#f538a0', '#a142f4', '#795548', '#607d8b', '#9e9e9e'];

  return (
    <div style={{ maxWidth: '1400px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid #dadce0', paddingBottom: 16 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 400 }}>Billing Overview</Title>
      </div>
      
      {/* Filters Section */}
      <Card style={{ marginBottom: 24, borderColor: '#dadce0', borderRadius: 8 }}>
        <Space wrap size="middle">
          <div>
            <div style={{ marginBottom: 4 }}><Text type="secondary">Date Range</Text></div>
            <RangePicker 
              value={dateRange} 
              onChange={(dates) => dates && setDateRange(dates)} 
              allowClear={false}
              presets={[
                { label: 'Last 1 day', value: [dayjs().subtract(1, 'day'), dayjs()] },
                { label: 'Last 3 days', value: [dayjs().subtract(3, 'day'), dayjs()] },
                { label: 'Last 7 days', value: [dayjs().subtract(7, 'day'), dayjs()] },
              ]}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}><Text type="secondary">Project ID</Text></div>
            <Input 
              placeholder="Filter by Project ID" 
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              style={{ width: 200 }}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}><Text type="secondary">Billing Account ID</Text></div>
            <Input 
              placeholder="Filter by Billing ID" 
              value={billingId}
              onChange={(e) => setBillingId(e.target.value)}
              style={{ width: 180 }}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}><Text type="secondary">Service</Text></div>
            <Input 
              placeholder="e.g. Vertex AI" 
              value={serviceDescription}
              onChange={(e) => setServiceDescription(e.target.value)}
              style={{ width: 160 }}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}><Text type="secondary">Cost Threshold</Text></div>
            <Select 
              value={minCost} 
              onChange={setMinCost}
              style={{ width: 120 }}
            >
              <Option value={0}>All Costs</Option>
              <Option value={10000}>{'>'} $10K</Option>
              <Option value={20000}>{'>'} $20K</Option>
              <Option value={50000}>{'>'} $50K</Option>
            </Select>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%' }}>
            <Button type="primary" icon={<SearchOutlined />} onClick={fetchData} style={{ marginTop: 26 }}>
              Apply Filters
            </Button>
          </div>
        </Space>
      </Card>

      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8, height: '100%' }}>
            <Text type="secondary">Total Cost (Selected Period)</Text>
            <Title level={2} style={{ margin: '8px 0 0 0', color: '#1a73e8' }}>
              ${totalCost.toFixed(2)}
            </Title>
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8, height: '100%' }}>
            <Text type="secondary">Active Projects</Text>
            <Title level={2} style={{ margin: '8px 0 0 0' }}>
              {usageData.length}
            </Title>
          </Card>
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Daily Usage Trend by Project" bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8 }}>
            <div style={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={processedTrendData} margin={{ top: 20, right: 30, left: 40, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `$${value}`} width={80} />
                  <Tooltip 
                    formatter={(value, name) => [`$${Number(value).toFixed(2)}`, name === 'cost' ? 'Total Cost' : name]} 
                    labelStyle={{ fontWeight: 'bold', marginBottom: '8px' }}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 2px 6px rgba(0,0,0,0.1)' }}
                  />
                  <Legend wrapperStyle={{ bottom: 0 }} />
                  {chartProjects.map((project, index) => (
                    <Bar 
                      key={project} 
                      dataKey={project} 
                      name={project} 
                      stackId="a" 
                      fill={projectColors[index % projectColors.length]} 
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Cost by Project (Histogram)" bordered={true} style={{ borderColor: '#dadce0', borderRadius: 8 }}>
            <div style={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={usageData.slice(0, 10)} margin={{ top: 20, right: 30, left: 40, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis 
                    dataKey="project_id" 
                    tick={{ fontSize: 11 }} 
                    interval={0}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `$${value}`} width={80} />
                  <Tooltip 
                    formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Total Cost']} 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #dadce0' }}
                  />
                  <Legend wrapperStyle={{ bottom: 0 }} />
                  <Bar dataKey="cost" name="Total Cost" fill="#34a853" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Table Section */}
      <div style={{ border: '1px solid #dadce0', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #dadce0', backgroundColor: '#f8f9fa', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text strong>Project Usage Details</Text>
          <Button icon={<DownloadOutlined />} onClick={handleDownloadExcel} size="small">
            Export to Excel
          </Button>
        </div>
        <Table 
          dataSource={usageData} 
          columns={columns} 
          rowKey="project_id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="middle"
          scroll={{ x: 'max-content' }}
        />
      </div>
    </div>
  );
};

export default Dashboard;
