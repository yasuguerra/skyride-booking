import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { Card } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { AlertCircle, Upload, Download, CheckCircle, Clock, XCircle, Plane, Calendar, DollarSign } from 'lucide-react';
import { useToast } from './hooks/use-toast';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-sky-50 to-blue-100">
        <nav className="bg-white shadow-sm border-b border-sky-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Plane className="h-8 w-8 text-sky-600 mr-3" />
                <h1 className="text-xl font-bold text-gray-900">Charter Aviation System</h1>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/" className="text-gray-700 hover:text-sky-600 px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </Link>
                <Link to="/admin" className="text-gray-700 hover:text-sky-600 px-3 py-2 rounded-md text-sm font-medium">
                  Admin
                </Link>
                <Link to="/ops" className="text-gray-700 hover:text-sky-600 px-3 py-2 rounded-md text-sm font-medium">
                  Operations
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="/ops" element={<OperationsPanel />} />
            <Route path="/quote/:id" element={<QuoteDetails />} />
            <Route path="/booking/:id" element={<BookingDetails />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    totalQuotes: 0,
    activeBookings: 0,
    availableAircraft: 0,
    recentActivity: []
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // In a real app, this would be a proper dashboard API endpoint
      setStats({
        totalQuotes: 45,
        activeBookings: 12,
        availableAircraft: 8,
        recentActivity: [
          { id: 1, type: 'quote', message: 'New quote created for PTY → BOC', time: '2 hours ago' },
          { id: 2, type: 'booking', message: 'Booking confirmed for Sky Ride Charter', time: '4 hours ago' },
          { id: 3, type: 'import', message: 'Aircraft data imported successfully', time: '1 day ago' }
        ]
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h2>
        <p className="text-gray-600">Overview of your charter aviation system</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 bg-gradient-to-br from-blue-50 to-sky-100 border-sky-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-sky-500 text-white">
              <DollarSign className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Quotes</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalQuotes}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-100 border-emerald-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-emerald-500 text-white">
              <CheckCircle className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Bookings</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeBookings}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-violet-100 border-violet-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-violet-500 text-white">
              <Plane className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Available Aircraft</p>
              <p className="text-2xl font-bold text-gray-900">{stats.availableAircraft}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {stats.recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="p-2 rounded-full bg-blue-100 text-blue-600 mr-3">
                {activity.type === 'quote' && <DollarSign className="h-4 w-4" />}
                {activity.type === 'booking' && <CheckCircle className="h-4 w-4" />}
                {activity.type === 'import' && <Upload className="h-4 w-4" />}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                <p className="text-xs text-gray-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function AdminPanel() {
  const [importRuns, setImportRuns] = useState([]);
  const { toast } = useToast();

  const handleFileImport = async (importType, file) => {
    if (!file) {
      toast({
        title: "Error",
        description: "Please select a file to import",
        variant: "destructive"
      });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/import/${importType}`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        toast({
          title: "Import Started",
          description: `${result.success_count} records processed successfully, ${result.error_count} errors`,
        });
        
        // Add to import runs list
        setImportRuns(prev => [{
          id: result.import_run_id,
          type: importType,
          status: 'COMPLETED',
          success_count: result.success_count,
          error_count: result.error_count,
          created_at: new Date().toISOString()
        }, ...prev]);
      } else {
        throw new Error(result.detail || 'Import failed');
      }
    } catch (error) {
      toast({
        title: "Import Failed",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const downloadSampleTemplate = (templateType) => {
    // In a real app, this would download actual templates
    const templates = {
      operators: 'operator,email,phone,base_airport\nSky Ride Charter,info@skyride.com,+507-1234-5678,PTY\nAero Panama,contact@aeropanama.com,+507-8765-4321,PAC',
      aircraft: 'name,operator,type,capacity,pets_allowed,ground_time_price_usd,product_link\nCessna Citation X,Sky Ride Charter,Citation X,12,true,150,https://example.com/citation\nBeechcraft King Air,Aero Panama,King Air 350,9,false,120,https://example.com/kingair',
      flights: 'id,flight_title,airplane_id,operator_id,flight_duration_min,price_without_itbms,itbms,total_price_one_way,departure_days,max_load_weight_lbs,description\n1,PTY – BOC,Cessna Citation X,Sky Ride Charter,45,1200,84,1284,Mon-Fri,2000,Daily flight to Bocas del Toro\n2,PTY / CHX,Beechcraft King Air,Aero Panama,60,1500,105,1605,Daily,1800,Charter to Changuinola'
    };

    const content = templates[templateType];
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${templateType}_template.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Admin Panel</h2>
        <p className="text-gray-600">Import data and manage system configuration</p>
      </div>

      <Tabs defaultValue="imports" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="imports">Data Imports</TabsTrigger>
          <TabsTrigger value="pricebook">Price Book</TabsTrigger>
          <TabsTrigger value="taxes">Taxes & Fees</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="imports" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Import</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ImportSection
                title="Operators"
                description="Import operator/charter companies"
                importType="operators"
                onImport={handleFileImport}
                onDownloadTemplate={() => downloadSampleTemplate('operators')}
              />
              
              <ImportSection
                title="Aircraft"
                description="Import aircraft fleet data"
                importType="aircraft"
                onImport={handleFileImport}
                onDownloadTemplate={() => downloadSampleTemplate('aircraft')}
              />
              
              <ImportSection
                title="Flights/Listings"
                description="Import flight listings and routes"
                importType="flights"
                onImport={handleFileImport}
                onDownloadTemplate={() => downloadSampleTemplate('flights')}
              />
            </div>

            {/* Import History */}
            {importRuns.length > 0 && (
              <div className="mt-8">
                <h4 className="text-md font-semibold text-gray-900 mb-3">Recent Imports</h4>
                <div className="space-y-2">
                  {importRuns.map((run) => (
                    <div key={run.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <span className="font-medium text-gray-900">{run.type}</span>
                        <span className="text-sm text-gray-500 ml-2">
                          {new Date(run.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={run.error_count > 0 ? "destructive" : "default"}>
                          {run.success_count} success, {run.error_count} errors
                        </Badge>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="pricebook" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Price Book Management</h3>
            <div className="flex space-x-4">
              <Button className="bg-sky-600 hover:bg-sky-700">
                <Upload className="h-4 w-4 mr-2" />
                Import Prices
              </Button>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Prices
              </Button>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="taxes" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Taxes & Surcharges</h3>
            <p className="text-gray-600">Configure tax rates and surcharges</p>
            <div className="mt-4 space-y-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">ITBMS (Panama Tax)</span>
                    <span className="text-sm text-gray-500 block">7% tax on charter flights</span>
                  </div>
                  <Badge>7%</Badge>
                </div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">Service Fee</span>
                    <span className="text-sm text-gray-500 block">Platform service fee</span>
                  </div>
                  <Badge>5%</Badge>
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
            <SystemHealthCheck />
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ImportSection({ title, description, importType, onImport, onDownloadTemplate }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isImporting, setIsImporting] = useState(false);

  const handleImport = async () => {
    if (!selectedFile) return;
    
    setIsImporting(true);
    try {
      await onImport(importType, selectedFile);
      setSelectedFile(null);
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Card className="p-4">
      <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      
      <div className="space-y-3">
        <Input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={(e) => setSelectedFile(e.target.files[0])}
          disabled={isImporting}
        />
        
        <div className="flex space-x-2">
          <Button
            onClick={handleImport}
            disabled={!selectedFile || isImporting}
            size="sm"
            className="flex-1"
          >
            {isImporting ? (
              <>
                <Clock className="h-4 w-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Import
              </>
            )}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={onDownloadTemplate}
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}

function SystemHealthCheck() {
  const [healthStatus, setHealthStatus] = useState({
    database: 'checking',
    redis: 'checking',
    wompi: 'checking',
    chatrace: 'checking'
  });

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const health = await response.json();
      
      setHealthStatus({
        database: health.database === 'healthy' ? 'healthy' : 'error',
        redis: health.redis === 'healthy' ? 'healthy' : 'error',
        wompi: 'healthy', // Would check Wompi connectivity
        chatrace: 'healthy' // Would check Chatrace connectivity
      });
    } catch (error) {
      setHealthStatus({
        database: 'error',
        redis: 'error',
        wompi: 'error',
        chatrace: 'error'
      });
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500 animate-spin" />;
    }
  };

  return (
    <div className="space-y-3">
      {Object.entries(healthStatus).map(([service, status]) => (
        <div key={service} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="font-medium capitalize">{service}</span>
          <div className="flex items-center">
            {getStatusIcon(status)}
            <span className="ml-2 text-sm capitalize">{status}</span>
          </div>
        </div>
      ))}
      
      <Button onClick={checkSystemHealth} variant="outline" className="w-full mt-4">
        Refresh Status
      </Button>
    </div>
  );
}

function OperationsPanel() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Operations</h2>
        <p className="text-gray-600">Manage availability, bookings, and operations</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Availability Management</h3>
          <p className="text-gray-600 mb-4">Manage aircraft availability slots and schedules</p>
          <Button className="w-full bg-sky-600 hover:bg-sky-700">
            <Calendar className="h-4 w-4 mr-2" />
            Manage Schedules
          </Button>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quote Management</h3>
          <p className="text-gray-600 mb-4">Review and manage customer quotes</p>
          <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
            <DollarSign className="h-4 w-4 mr-2" />
            View Quotes
          </Button>
        </Card>
      </div>
    </div>
  );
}

function QuoteDetails() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Quote Details</h2>
      <p>Quote details will be displayed here</p>
    </div>
  );
}

function BookingDetails() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Booking Details</h2>
      <p>Booking details will be displayed here</p>
    </div>
  );
}

export default App;