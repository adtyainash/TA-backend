@echo off
echo 🚀 Starting deployment...

REM Build frontend
echo 📦 Building frontend...
cd frontend
call npm run build
cd ..

REM Start with PM2
echo 🔄 Starting applications with PM2...
pm2 start ecosystem.config.js

echo ✅ Deployment complete!
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo.
echo 📋 PM2 Commands:
echo   pm2 status          - Check status
echo   pm2 logs            - View logs
echo   pm2 restart all     - Restart all apps
echo   pm2 stop all        - Stop all apps

pause 