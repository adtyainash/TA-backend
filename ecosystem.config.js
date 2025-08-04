const path = require("path");

module.exports = {
  apps: [
    {
      name: "fastapi-app",
      script: "uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000",
      interpreter: path.resolve(__dirname, "venv/bin/python"),
      watch: false,
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "react-frontend",
      script: "npm",
      args: "run serve",
      cwd: path.resolve(__dirname, "frontend"),
      env: {
        NODE_ENV: "production",
        PORT: 3000
      },
      instances: 1,
      exec_mode: "fork"
    }
  ],
};
