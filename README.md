# SkyRide Charter Booking Platform 🚁

A comprehensive charter flight booking platform with marketplace functionality, hosted quotes, and integrated payment processing.

## 🎯 MVP Features Complete

### ✅ Core Booking Flow
- **Marketplace Listings** - Browse available charter flights with transparent pricing
- **Hosted Quotes** - Unique tokenized quotes with expiration timers (`/q/{token}`)
- **Hold System** - 24-hour booking holds with optional deposits
- **Payment Processing** - Wompi Banistmo integration with webhook support
- **Price Parity** - Transparent Base Price + Service Fee breakdown

### ✅ Platform Features
- **Sky Ride Protection** - Weather delays, aircraft substitution, 24/7 support
- **Price Match Guarantee** - Beat any legitimate quote by 5%
- **Admin Dashboard** - Operator portal with listings and booking management
- **WhatsApp Integration** - Chatrace templates and webhook processing
- **n8n Hooks** - API endpoints for external automation workflows

### ✅ Technical Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI components
- **Backend**: FastAPI + Motor (MongoDB async driver)
- **Database**: MongoDB with UUID-based models
- **Payments**: Wompi Banistmo (primary) + Yappy (feature flagged)
- **Messaging**: Chatrace WhatsApp API integration
- **Security**: CORS, CSP headers, webhook signature verification

## 🚀 Quick Start

### Test the Platform
```bash
# Health check
curl https://charter-hub-1.preview.emergentagent.com/api/health

# Test listings
curl https://charter-hub-1.preview.emergentagent.com/api/listings
```

## 📊 Sample Data Included

The platform comes with seeded sample data:

- **2 Operators**: Panama Elite Aviation, Sky Charter Panama
- **3 Aircraft**: Bell 407, Bell 206, Airbus AS350  
- **4 Routes**: Panama City → San Carlos, Bocas del Toro, David, Colon
- **4 Charter Listings**: Various pricing from $2,940 - $8,820

## 🔗 Key URLs

- **Homepage**: `/` - Flight search and listings
- **Hosted Quote**: `/q/{token}` - Individual quote pages with timers
- **Checkout**: `/checkout/{orderId}` - Payment processing
- **Admin Dashboard**: `/admin` or `/ops` - Operator portal
- **Success Page**: `/success` - Post-payment confirmation

## 🏆 Success Criteria Met

✅ **Quote Creation**: Under 60 seconds with guaranteed pricing
✅ **Payment Processing**: Wompi integration with webhook automation  
✅ **Hold System**: 24-hour holds with countdown timers
✅ **Price Transparency**: Clear base + service fee breakdown
✅ **Protection Features**: Sky Ride Protection included
✅ **Admin Tools**: Operator dashboard for management
✅ **Integration Ready**: WhatsApp, n8n, WordPress compatibility

The platform is production-ready and meets all MVP requirements for the SkyRide charter booking marketplace.
