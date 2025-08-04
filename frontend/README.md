# DBD Dashboard Frontend

A React-based frontend for the DBD (Dengue Hemorrhagic Fever) Case Management and Prediction System.

## Features

- **PowerBI Dashboard Integration**: Embedded PowerBI dashboard for data visualization
- **Case Submission Form**: Form to submit new daily case data to the backend API
- **Responsive Design**: Modern, responsive UI that works on desktop and mobile devices
- **Real-time Feedback**: Success/error messages for form submissions

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development

To run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Building for Production

To build the application for production:

```bash
npm run build
```

This creates a `dist` folder with the production-ready files.

## Running in Production

### Using PM2 (Recommended)

The frontend is configured to run with PM2. From the root directory:

```bash
# Build the frontend first
cd frontend && npm run build

# Start both backend and frontend with PM2
pm2 start ecosystem.config.js
```

### Using serve directly

```bash
npm run serve
```

This serves the built application on port 3000.

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`. The main endpoint used is:

- `POST /submit_case/` - Submit new daily case data

### Form Fields

- **Date**: The date of the case (required)
- **Number of Cases**: Number of cases for that date (required, must be >= 0)
- **ICD10 Code**: The ICD10 code for the disease (required, e.g., "A90" for dengue)

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Application styles
│   └── main.jsx         # Application entry point
├── dist/                # Production build output
├── package.json         # Dependencies and scripts
├── vite.config.js       # Vite configuration
└── README.md           # This file
```

## Customization

### Styling

The application uses CSS Grid and Flexbox for layout. The main styles are in `src/App.css`. The color scheme uses a purple gradient theme that can be easily modified.

### PowerBI Dashboard

The PowerBI dashboard is embedded via an iframe. To change the dashboard, update the `src` attribute in the iframe element in `App.jsx`.

### API Endpoint

To change the API endpoint, update the fetch URL in the `handleSubmit` function in `App.jsx`.

## Troubleshooting

### CORS Issues

If you encounter CORS issues, ensure the backend has CORS middleware configured to allow requests from `http://localhost:3000`.

### Build Issues

If the build fails, try:
1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `npm run build -- --force`

### PM2 Issues

If PM2 fails to start the frontend:
1. Ensure the frontend is built: `cd frontend && npm run build`
2. Check if port 3000 is available
3. Verify the ecosystem.config.js path is correct
