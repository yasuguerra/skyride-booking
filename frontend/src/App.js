import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Badge } from "./components/ui/badge";
import { Calendar } from "./components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Separator } from "./components/ui/separator";
import { AlertCircle, Clock, Plane, MapPin, Users, Star, Shield, CheckCircle } from "lucide-react";
import { format } from "date-fns";
import { cn } from "./lib/utils";
import AdminDashboard from "./components/AdminDashboard";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utility function for API calls
const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await axios({
      url: `${API}${endpoint}`,
      method: options.method || 'GET',
      data: options.data,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

// HomePage Component
const HomePage = () => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    origin: '',
    destination: '',
    date: null,
    passengers: 1
  });
  const navigate = useNavigate();

  useEffect(() => {
    loadListings();
  }, []);

  const loadListings = async () => {
    try {
      const data = await apiCall('/listings', {
        params: {
          ...filters,
          date: filters.date ? format(filters.date, 'yyyy-MM-dd') : null,
          limit: 12
        }
      });
      setListings(data);
    } catch (error) {
      console.error('Failed to load listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setLoading(true);
    loadListings();
  };

  const handleQuoteRequest = async (listingId) => {
    try {
      const quoteData = {
        listingId,
        passengers: filters.passengers,
        departureDate: filters.date ? format(filters.date, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd')
      };
      
      const response = await apiCall('/quotes', {
        method: 'POST',
        data: quoteData
      });
      
      navigate(`/q/${response.token}`);
    } catch (error) {
      console.error('Failed to create quote:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sky Ride Branded Header */}
      <header className="sr-navbar sticky bg-white border-b border-gray-200 shadow-sr-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img 
                src="/brand/wordmark.svg" 
                alt="Sky Ride" 
                className="h-6 w-auto"
                onError={(e) => {
                  // Fallback to text if SVG fails
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <h1 className="text-2xl font-sr font-bold text-sr-primary hidden">
                Sky Ride
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Badge className="bg-sr-primary-light text-sr-primary border-sr-primary">
                <CheckCircle className="h-3 w-3 mr-1" />
                Live Platform
              </Badge>
              <Button className="btn-primary bg-sr-primary hover:bg-sr-accent text-white rounded-sr">
                Cotiza ahora
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section with Search */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Charter Your Next
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent block">
              Adventure
            </span>
          </h2>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Experience premium private aviation with transparent pricing, instant quotes, and guaranteed availability.
          </p>

          {/* Search Form */}
          <Card className="p-6 bg-white/90 backdrop-blur-sm border border-gray-200/50 shadow-xl">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="space-y-2">
                <Label htmlFor="origin">From</Label>
                <Input
                  id="origin"
                  placeholder="Origin city"
                  value={filters.origin}
                  onChange={(e) => setFilters({...filters, origin: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="destination">To</Label>
                <Input
                  id="destination"
                  placeholder="Destination city"
                  value={filters.destination}
                  onChange={(e) => setFilters({...filters, destination: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className={cn("justify-start text-left font-normal", !filters.date && "text-muted-foreground")}>
                      {filters.date ? format(filters.date, "MMM dd, yyyy") : "Select date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.date}
                      onSelect={(date) => setFilters({...filters, date})}
                      disabled={(date) => date < new Date()}
                    />
                  </PopoverContent>
                </Popover>
              </div>
              <div className="space-y-2">
                <Label>Passengers</Label>
                <Select value={filters.passengers.toString()} onValueChange={(value) => setFilters({...filters, passengers: parseInt(value)})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1,2,3,4,5,6,7,8].map(num => (
                      <SelectItem key={num} value={num.toString()}>{num} Passenger{num > 1 ? 's' : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={handleSearch} size="lg" className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              Search Flights
            </Button>
          </Card>
        </div>
      </section>

      {/* Listings Section */}
      <section className="py-16 px-4 bg-white/50">
        <div className="container mx-auto max-w-7xl">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-3xl font-bold text-gray-900">Available Flights</h3>
              <p className="text-gray-600 mt-2">Choose from our premium fleet</p>
            </div>
            <Badge variant="secondary" className="bg-blue-100 text-blue-700">
              {listings.length} flights available
            </Badge>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1,2,3,4,5,6].map(i => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-6">
                    <div className="h-48 bg-gray-200 rounded-lg mb-4"></div>
                    <div className="space-y-3">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-4 bg-gray-200 rounded w-full"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : listings.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No flights found</h3>
                <p className="text-gray-600">Try adjusting your search criteria</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {listings.map((listing) => (
                <Card key={listing.id} className="group hover:shadow-xl transition-all duration-300 border-0 bg-white/80 backdrop-blur-sm">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg text-gray-900">{listing.aircraft?.model}</CardTitle>
                        <CardDescription className="flex items-center mt-1">
                          <MapPin className="h-4 w-4 mr-1" />
                          {listing.route?.origin} → {listing.route?.destination}
                        </CardDescription>
                      </div>
                      {listing.featured && (
                        <Badge className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white">
                          <Star className="h-3 w-3 mr-1" />
                          Featured
                        </Badge>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        Up to {listing.maxPassengers} passengers
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {listing.confirmationSLA}h SLA
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="bg-green-50 text-green-700">
                        <Shield className="h-3 w-3 mr-1" />
                        Sky Ride Protection
                      </Badge>
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Base Price</span>
                        <span>${listing.basePrice?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Service Fee</span>
                        <span>${listing.serviceFee?.toLocaleString()}</span>
                      </div>
                      <Separator />
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-900">Total</span>
                        <span className="text-2xl font-bold text-blue-600">${listing.totalPrice?.toLocaleString()}</span>
                      </div>
                    </div>
                  </CardContent>

                  <CardFooter>
                    <Button 
                      onClick={() => handleQuoteRequest(listing.id)}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 group-hover:shadow-lg transition-all duration-300"
                    >
                      Get Quote Now
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="container mx-auto max-w-4xl text-center">
          <h3 className="text-3xl font-bold mb-12">Why Choose SkyRide?</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-4">
              <div className="bg-white/20 p-4 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                <Shield className="h-8 w-8" />
              </div>
              <h4 className="text-xl font-semibold">Price Match Guarantee</h4>
              <p className="text-blue-100">We match any legitimate quote and beat it by 5%</p>
            </div>
            <div className="space-y-4">
              <div className="bg-white/20 p-4 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                <Clock className="h-8 w-8" />
              </div>
              <h4 className="text-xl font-semibold">Instant Quotes</h4>
              <p className="text-blue-100">Get your quote in under 60 seconds with guaranteed pricing</p>
            </div>
            <div className="space-y-4">
              <div className="bg-white/20 p-4 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                <CheckCircle className="h-8 w-8" />
              </div>
              <h4 className="text-xl font-semibold">Sky Ride Protection</h4>
              <p className="text-blue-100">Full protection against cancellations and weather delays</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

// HostedQuote Component
const HostedQuote = () => {
  const { token } = useParams();
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [holdLoading, setHoldLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadQuote();
  }, [token]);

  useEffect(() => {
    if (quote && quote.expiresAt) {
      const timer = setInterval(() => {
        const now = new Date();
        const expiry = new Date(quote.expiresAt);
        const diff = expiry - now;
        
        if (diff <= 0) {
          setTimeLeft('EXPIRED');
          clearInterval(timer);
        } else {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);
          setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
        }
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [quote]);

  const loadQuote = async () => {
    try {
      const data = await apiCall(`/quotes/${token}`);
      setQuote(data);
    } catch (error) {
      if (error.response?.status === 404) {
        setError('Quote not found');
      } else if (error.response?.status === 410) {
        setError('Quote has expired');
      } else {
        setError('Failed to load quote');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateHold = async () => {
    setHoldLoading(true);
    try {
      await apiCall('/holds', {
        method: 'POST',
        data: { token }
      });
      
      // Create booking and redirect to checkout
      const bookingData = {
        quoteId: quote.id,
        operatorId: quote.listing.operatorId,
        totalAmount: quote.totalPrice,
        departureDate: quote.departureDate,
        returnDate: quote.returnDate
      };
      
      // For MVP, we'll simulate booking creation and redirect to checkout
      navigate(`/checkout/${quote.id}`);
    } catch (error) {
      console.error('Failed to create hold:', error);
    } finally {
      setHoldLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Loading your quote...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">{error}</h2>
            <Button onClick={() => navigate('/')} variant="outline">
              Return to Search
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button variant="outline" onClick={() => navigate('/')}>
            ← Back to Search
          </Button>
          <Badge className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-lg px-4 py-2">
            <Clock className="h-4 w-4 mr-2" />
            {timeLeft === 'EXPIRED' ? 'EXPIRED' : `Expires in: ${timeLeft}`}
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quote Details */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-2xl text-gray-900">Your Flight Quote</CardTitle>
                <CardDescription>Quote #{quote.token}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Route & Aircraft */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{quote.route.origin} → {quote.route.destination}</h3>
                    <p className="text-gray-600">{quote.aircraft.model} • Up to {quote.aircraft.capacity} passengers</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Operated by</p>
                    <p className="font-semibold">{quote.operator.name}</p>
                  </div>
                </div>

                <Separator />

                {/* Flight Details */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-gray-600">Departure</Label>
                    <p className="font-semibold">{format(new Date(quote.departureDate), 'MMM dd, yyyy')}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">Passengers</Label>
                    <p className="font-semibold">{quote.passengers}</p>
                  </div>
                </div>

                {/* Pricing Breakdown */}
                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                  <div className="flex justify-between">
                    <span>Base Price</span>
                    <span>${quote.basePrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Service Fee</span>
                    <span>${quote.serviceFee.toLocaleString()}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total Price</span>
                    <span className="text-blue-600">${quote.totalPrice.toLocaleString()}</span>
                  </div>
                </div>

                {/* Features */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    <Shield className="h-3 w-3 mr-1" />
                    Sky Ride Protection
                  </Badge>
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    Price Match Guarantee
                  </Badge>
                  <Badge variant="outline" className="bg-purple-50 text-purple-700">
                    Instant Confirmation
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Booking Actions */}
          <div className="space-y-6">
            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Reserve Your Flight</CardTitle>
                <CardDescription>Secure this quote with a hold</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">${quote.totalPrice.toLocaleString()}</p>
                  <p className="text-sm text-gray-600">Total Price</p>
                </div>
                
                <Button 
                  onClick={handleCreateHold}
                  disabled={holdLoading || timeLeft === 'EXPIRED'}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                  size="lg"
                >
                  {holdLoading ? 'Processing...' : 'Book Now'}
                </Button>
                
                <p className="text-xs text-gray-500 text-center">
                  Creates a 24-hour hold • No payment required yet
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-sm">Protection Included</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                <div className="flex items-center text-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Weather delay protection
                </div>
                <div className="flex items-center text-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Aircraft substitution guarantee  
                </div>
                <div className="flex items-center text-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  24/7 concierge support
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// Checkout Component
const Checkout = () => {
  const { orderId } = useParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleWompiCheckout = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiCall('/checkout', {
        method: 'POST',
        data: {
          orderId,
          provider: 'WOMPI'
        }
      });
      
      if (response.paymentLinkUrl) {
        window.location.href = response.paymentLinkUrl;
      }
    } catch (error) {
      setError('Failed to create payment link. Please try again.');
      console.error('Checkout error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-8">
      <div className="container mx-auto px-4 max-w-2xl">
        <Card className="bg-white/90 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Complete Your Booking</CardTitle>
            <CardDescription className="text-center">Order #{orderId}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            )}
            
            <div className="text-center space-y-4">
              <p className="text-gray-600">Choose your payment method to complete the booking</p>
              
              <Button 
                onClick={handleWompiCheckout}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                size="lg"
              >
                {loading ? 'Processing...' : 'Pay with Wompi'}
              </Button>
              
              <p className="text-xs text-gray-500">
                Secure payment powered by Wompi Banistmo
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Success Page
const Success = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Confirmed!</h2>
          <p className="text-gray-600 mb-6">
            Your flight has been booked successfully. You'll receive a confirmation email shortly.
          </p>
          <Button onClick={() => navigate('/')} className="w-full">
            Return to Home
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/q/:token" element={<HostedQuote />} />
          <Route path="/checkout/:orderId" element={<Checkout />} />
          <Route path="/success" element={<Success />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/ops" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;