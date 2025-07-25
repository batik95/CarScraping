# CarScraping Unraid Implementation

This directory contains all files needed for complete Unraid integration of CarScraping.

## 📁 Files Overview

### Core Container Files
- **`../docker/Dockerfile.unraid`** - Multi-service container with PostgreSQL + Redis + App
- **`../docker/supervisord.conf`** - Process management configuration  
- **`../docker/entrypoint.sh`** - Initialization script with database setup
- **`../docker/build-test-unraid.sh`** - Build and test automation script

### Unraid Integration
- **`CarScraping.xml`** - Complete Unraid Community Applications template
- **`install-guide.md`** - Comprehensive installation and troubleshooting guide
- **`README-Unraid.md`** - Original Unraid documentation (preserved)
- **`ICON-README.md`** - Instructions for creating application icon

### Backup Files  
- **`CarScraping.xml.backup`** - Original template before enhancement
- **`icon-placeholder.md`** - Icon placeholder documentation

## 🚀 Quick Setup

### For End Users (Unraid Community Applications)
1. Search "CarScraping" in Community Applications
2. Click Install
3. Configure ports and directories
4. Start container
5. Access web interface at `http://unraid-ip:8787`

### For Developers (Manual Build)
```bash
# Build Unraid container
docker build -f docker/Dockerfile.unraid -t carscraping:unraid .

# Test container
mkdir -p test-dirs/{config,data,logs}
docker run -p 8787:8787 \
  -v $(pwd)/test-dirs/config:/config \
  -v $(pwd)/test-dirs/data:/data \
  -v $(pwd)/test-dirs/logs:/logs \
  carscraping:unraid
```

## ✨ Key Features

### All-in-One Container
- **PostgreSQL 15** embedded for data persistence
- **Redis 7** embedded for caching
- **Supervisord** for reliable process management
- **Automatic initialization** of database and configuration

### Unraid Optimized
- **Volume mapping** for persistent data (`/config`, `/data`, `/logs`)
- **Environment variables** for easy configuration
- **Health checks** for monitoring
- **User/Group ID** support for proper permissions

### Zero Dependencies
- **No docker-compose** required
- **No external databases** needed
- **Single container** deployment
- **Automatic database setup** on first run

## 🔧 Configuration

### Environment Variables
```bash
SCRAPING_INTERVAL=24      # Scraping frequency in hours
LOG_LEVEL=INFO           # Logging level
DEBUG=false              # Debug mode
MAX_RETRIES=3            # Retry attempts for failed scraping
REQUEST_DELAY=1.0        # Delay between HTTP requests
DATABASE_URL=            # External DB (optional, embedded by default)
PUID=99                  # User ID for permissions
PGID=100                 # Group ID for permissions
```

### Directory Structure
```
/mnt/user/appdata/carscraping/
├── config/              # Application configuration
│   └── .env            # Environment settings
├── data/               # Database and cache data
│   ├── postgres/       # PostgreSQL data
│   └── redis/          # Redis data
└── logs/               # Application logs
    ├── app.log         # Main application
    ├── postgresql.log  # Database logs
    └── redis.log       # Cache logs
```

## 📊 Monitoring

### Health Check Endpoint
```bash
curl http://unraid-ip:8787/health
```

### Response Example
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production", 
  "mode": "unraid",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "disk_space": {
      "total_gb": 100.0,
      "used_gb": 10.5,
      "free_gb": 89.5,
      "usage_percent": 10.5
    }
  }
}
```

## 🔄 Build Process

The Unraid container includes:

1. **Base Image**: Python 3.11 slim
2. **System Dependencies**: PostgreSQL, Redis, Supervisor
3. **Python Dependencies**: FastAPI, SQLAlchemy, etc.
4. **Configuration Files**: Supervisord, entrypoint script
5. **Initialization**: Database setup, user creation
6. **Health Checks**: Application and service monitoring

## 🐛 Troubleshooting

### Common Issues

**Container won't start**
- Check port conflicts (8787, 5432, 6379)
- Verify directory permissions
- Review container logs: `docker logs CarScraping`

**Database connection failed**
- Wait for full initialization (2-3 minutes first start)
- Check PostgreSQL logs in `/logs/postgresql.log`
- Verify disk space availability

**Scraping not working**
- Check internet connectivity
- Review scraping logs
- Adjust `REQUEST_DELAY` if rate limited

### Log Locations
```bash
# Container logs
docker logs CarScraping

# Application logs
tail -f /mnt/user/appdata/carscraping/logs/app.log

# Database logs  
tail -f /mnt/user/appdata/carscraping/logs/postgresql.log
```

## 📝 Development Notes

### Architecture Decisions
- **Supervisord vs systemd**: Chosen for container compatibility
- **Embedded vs External DB**: Supports both modes for flexibility  
- **Single vs Multi-container**: Single for Unraid simplicity
- **Health checks**: Enhanced for Unraid monitoring integration

### Future Enhancements
- [ ] Automated icon generation
- [ ] Grafana dashboard integration  
- [ ] Backup/restore automation
- [ ] Multiple database backend support
- [ ] Advanced monitoring metrics

## 📚 Documentation

- **Installation Guide**: `install-guide.md` - Complete setup instructions
- **Original Docs**: `README-Unraid.md` - Legacy documentation
- **API Documentation**: Available at `http://unraid-ip:8787/docs`
- **GitHub Repository**: https://github.com/batik95/CarScraping

## 🤝 Contributing

To contribute to the Unraid implementation:

1. Test changes with the build script: `docker/build-test-unraid.sh`
2. Update documentation as needed
3. Validate XML template with Unraid community standards  
4. Ensure backward compatibility with existing installations

---

**Template Version**: 1.0.0 
**Container Tag**: `batik95/carscraping:unraid`
**Minimum Unraid**: 6.9.0
**Last Updated**: 2024-01-XX