# RedSignal C2 Platform

🔴 **RedSignal** is a comprehensive Command and Control (C2) emulation platform designed for cybersecurity education, red team exercises, and security research. It provides a realistic C2 framework while maintaining safety through built-in restrictions and simulation modes.

## ⚠️ IMPORTANT DISCLAIMER

**This tool is for educational and authorized security testing purposes only.**

- Only use on systems you own or have explicit permission to test
- Never use for malicious activities or unauthorized access
- Always comply with local laws and regulations
- The authors are not responsible for misuse of this software

## 🚀 Features

### Core Capabilities
- **Multi-Client C2 Architecture**: Support for multiple simultaneous agents
- **Real-time Communication**: Beacon-based communication with configurable intervals
- **Web Dashboard**: Modern web interface for managing clients and commands
- **RESTful API**: Complete API for programmatic interaction
- **Safe Execution**: Built-in safety mechanisms and simulation modes

### Command Types
- **System Information Collection**: Gather comprehensive system details
- **File System Reconnaissance**: Safe directory listing and file analysis
- **Shell Command Execution**: Controlled command execution with safety filters
- **Data Exfiltration Simulation**: Simulate data extraction techniques
- **Persistence Checking**: Identify potential persistence mechanisms
- **Custom Beacon Management**: Flexible beacon configuration

### Security Features
- **Path Restrictions**: Prevents access to sensitive system directories
- **Command Filtering**: Blocks dangerous commands automatically
- **Simulation Mode**: Many operations run in simulation-only mode
- **Audit Logging**: Comprehensive logging of all activities
- **API Authentication**: Secure API access with key-based authentication

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended)
- 1GB disk space
- Network connectivity between server and clients

### Python Dependencies

- `fastapi>=0.68.0`
- `uvicorn>=0.15.0`
- `aiohttp>=3.8.0`
- `psutil>=5.8.0`
- `pyyaml>=5.4.0`
- `cryptography>=3.4.0`
- `python-multipart>=0.0.5`

## 🛠️ Installation

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/redsignal.git
cd redsignal

# Install dependencies
pip install -r requirements.txt

# Create configuration directories
mkdir -p config logs

# Copy example configurations
cp config/server_config.yaml.example config/server_config.yaml
cp config/client_config.yaml.example config/client_config.yaml

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/