# Smite - Tunneling Control Panel

<div align="center">
  <img src="assets/SmiteD.png" alt="Smite Logo" width="200"/>
  
  **A modern, Docker-first tunneling control panel for managing tunnels (TCP, UDP, gRPC, TCPMux, Rathole).**
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## 🚀 Features

- **Multiple Tunnel Types**: Support for TCP, UDP, gRPC, TCPMux, and Rathole
- **Docker-First**: Easy deployment with Docker Compose
- **Web UI**: Modern, intuitive web interface for tunnel management
- **CLI Tools**: Powerful command-line tools for management
- **Node Support**: Easy reverse tunnel setup with Rathole nodes
- **GOST Forwarding**: Direct forwarding without nodes for better performance

---

## 🛠️ Tech Stack

- **Backend**: Python (FastAPI), SQLAlchemy, Alembic
- **Frontend**: React, TypeScript, Tailwind CSS
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx
- **Tunneling**: GOST, Rathole
- **Database**: SQLite
- **SSL/TLS**: Let's Encrypt (Certbot)

---

## 📋 Prerequisites

- Docker and Docker Compose installed
- For Iran servers, install Docker first:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/manageitir/docker/main/install-ubuntu.sh | sh
  ```

---

## 🔧 Panel Installation

### Quick Install

```bash
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/zZedix/Smite/master/scripts/install.sh)"
```

### Manual Install

1. Clone the repository:
```bash
git clone https://github.com/zZedix/Smite.git
cd Smite
```

2. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Install CLI tools:
```bash
sudo bash cli/install_cli.sh
```

4. Start services:
```bash
docker compose up -d
```

5. Create admin user:
```bash
smite admin create
```

6. Access the web interface at `http://localhost:8000`

---

## 🖥️ Node Installation

> **Note**: Nodes are used for **Rathole** tunnels, providing easy reverse tunnel functionality. For GOST tunnels (TCP, UDP, gRPC, TCPMux), you can forward directly without a node.

### Quick Install

```bash
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/zZedix/Smite/master/scripts/smite-node.sh)"
```

The installer will prompt for:
- Panel CA certificate path
- Panel address (host:port)
- Node API port (default: 8888)
- Node name (default: node-1)

### Manual Install

1. Navigate to node directory:
```bash
cd node
```

2. Copy Panel CA certificate:
```bash
mkdir -p certs
cp /path/to/panel/ca.crt certs/ca.crt
```

3. Create `.env` file:
```bash
cat > .env << EOF
NODE_API_PORT=8888
NODE_NAME=node-1
PANEL_CA_PATH=/etc/smite-node/certs/ca.crt
PANEL_ADDRESS=panel.example.com:443
EOF
```

4. Start node:
```bash
docker compose up -d
```

---

## 🛠️ CLI Tools

### Panel CLI (`smite`)
```bash
smite admin create      # Create admin user
smite status            # Show system status
smite update            # Update and restart
smite logs              # View logs
```

### Node CLI (`smite-node`)
```bash
smite-node status       # Show node status
smite-node update       # Update node
smite-node logs         # View logs
```

---

## 📖 Tunnel Types

### GOST Tunnels (Direct Forwarding)
- **TCP**: Simple TCP forwarding
- **UDP**: UDP packet forwarding
- **gRPC**: gRPC protocol forwarding
- **TCPMux**: TCP multiplexing for multiple connections

These tunnels work directly without requiring a node - they forward traffic from the panel to the target server.

### Rathole Tunnels (Reverse Tunnel)
Rathole tunnels require a node and provide easy reverse tunnel functionality. The node connects to the panel, allowing you to expose services running on the node's network through the panel.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💰 Donations

If you find Smite useful and want to support its development, consider making a donation:

### Cryptocurrency Donations

- **Bitcoin (BTC)**: `bc1q637gahjssmv9g3903j88tn6uyy0w2pwuvsp5k0`
- **Ethereum (ETH)**: `0x5B2eE8970E3B233F79D8c765E75f0705278098a0`
- **Tron (TRX)**: `TSAsosG9oHMAjAr3JxPQStj32uAgAUmMp3`
- **USDT (BEP20)**: `0x5B2eE8970E3B233F79D8c765E75f0705278098a0`
- **TON**: `UQA-95WAUn_8pig7rsA9mqnuM5juEswKONSlu-jkbUBUhku6`

### Other Ways to Support

- ⭐ Star the repository if you find it useful
- 🐛 Report bugs and suggest improvements
- 📖 Improve documentation and translations
- 🔗 Share with others who might benefit

---

<div align="center">
  
  **Made with ❤️ by [zZedix](https://github.com/zZedix)**
  
  *Securing the digital world, one line of code at a time!*
  
</div>
