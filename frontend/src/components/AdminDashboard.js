import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { 
  Users, 
  Plane, 
  MapPin, 
  Clock, 
  DollarSign, 
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Settings
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalListings: 0,
    activeQuotes: 0,
    recentBookings: 0,
    revenue: 0
  });
  const [listings, setListings] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load listings
      const listingsResponse = await axios.get(`${API}/listings?limit=50`);
      setListings(listingsResponse.data);
      
      // Calculate stats from listings
      const activeListings = listingsResponse.data.filter(l => l.status === 'ACTIVE');
      
      setStats({
        totalListings: activeListings.length,
        activeQuotes: 12, // Mock data for demo
        recentBookings: 8,
        revenue: 125000
      });
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, description, trend }) => (
    <Card className="card bg-white shadow-sr">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-sr font-medium text-sr-primary">{title}</CardTitle>
        <Icon className="h-4 w-4 text-sr-accent" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-sr font-bold text-sr-primary">{value}</div>
        {description && (
          <p className="text-xs text-gray-600 font-sr mt-1">{description}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2 text-xs">
            <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            <span className="text-green-500 font-sr">{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="container mx-auto max-w-7xl">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sr-accent"></div>
            <span className="ml-3 text-gray-600 font-sr">Loading dashboard...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="container mx-auto max-w-7xl">
        
        {/* Sky Ride Admin Header */}
        <div className="sr-admin-header bg-sr-primary text-white p-6 rounded-sr mb-8 shadow-sr">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-sr font-bold">SkyRide Admin</h1>
              <p className="text-sr-accent-light mt-1 font-sr">Portal Operador - Charter Operations Dashboard</p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge className="bg-green-100 text-green-700 border-green-200 font-sr">
                <CheckCircle className="h-3 w-3 mr-1" />
                Platform Active
              </Badge>
              <Button variant="outline" size="sm" className="border-white text-white hover:bg-white hover:text-sr-primary">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Active Listings"
            value={stats.totalListings}
            icon={Plane}
            description="Charter flights available"
            trend="+2 this week"
          />
          <StatCard
            title="Active Quotes"
            value={stats.activeQuotes}
            icon={Clock}
            description="Pending customer quotes"
            trend="+15% vs last week"
          />
          <StatCard
            title="Bookings (30d)"
            value={stats.recentBookings}
            icon={Users}
            description="Confirmed bookings"
            trend="+25% vs last month"
          />
          <StatCard
            title="Revenue (30d)"
            value={`$${stats.revenue.toLocaleString()}`}
            icon={DollarSign}
            description="Total booking revenue"
            trend="+18% vs last month"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Recent Listings */}
          <Card>
            <CardHeader>
              <CardTitle>Active Charter Listings</CardTitle>
              <CardDescription>Current flight offerings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {listings.slice(0, 6).map((listing, index) => (
                <div key={listing._id || index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium">{listing.aircraft?.model || 'Unknown Aircraft'}</h4>
                      {listing.featured && (
                        <Badge className="bg-yellow-100 text-yellow-800 text-xs">Featured</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 flex items-center">
                      <MapPin className="h-3 w-3 mr-1" />
                      {listing.route?.origin} → {listing.route?.destination}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Up to {listing.maxPassengers} passengers • {listing.confirmationSLA}h SLA
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-blue-600">${listing.totalPrice?.toLocaleString()}</p>
                    <Badge 
                      variant={listing.status === 'ACTIVE' ? 'default' : 'secondary'}
                      className="text-xs mt-1"
                    >
                      {listing.status || 'UNKNOWN'}
                    </Badge>
                  </div>
                </div>
              ))}
              
              {listings.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Plane className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No listings found</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle>System Status</CardTitle>
              <CardDescription>Platform health and integrations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              
              {/* Service Status */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">API Backend</span>
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Online
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Database</span>
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Connected
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Wompi Integration</span>
                  <Badge className="bg-yellow-100 text-yellow-800">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    DRY_RUN
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">WhatsApp (Chatrace)</span>
                  <Badge className="bg-yellow-100 text-yellow-800">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Configured
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Empty Legs</span>
                  <Badge variant="secondary">
                    Disabled
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Yappy Payments</span>
                  <Badge variant="secondary">
                    Coming Soon
                  </Badge>
                </div>
              </div>
              
              <Separator />
              
              {/* Quick Actions */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium mb-3">Quick Actions</h4>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Plane className="h-4 w-4 mr-2" />
                  Add New Listing
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  View All Bookings
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-2" />
                  System Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;