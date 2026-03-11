"""
Web interface for RedSignal C2 server.
Provides HTML dashboard for managing clients and commands.
"""

from typing import List, Dict, Any
import json
from datetime import datetime


class WebInterface:
    """Generates HTML interfaces for the C2 server."""

    def __init__(self):
        self.base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RedSignal C2 Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a; color: #e0e0e0; line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: #2d2d2d; padding: 20px; border-radius: 8px; 
            margin-bottom: 30px; border-left: 4px solid #ff6b6b;
        }
        .nav { display: flex; gap: 20px; margin-top: 15px; }
        .nav a { 
            color: #4ecdc4; text-decoration: none; padding: 8px 16px;
            border-radius: 4px; transition: background 0.3s;
        }
        .nav a:hover { background: #3a3a3a; }
        .card { 
            background: #2d2d2d; padding: 20px; border-radius: 8px; 
            margin-bottom: 20px; border-left: 4px solid #4ecdc4;
        }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-card { 
            background: #3a3a3a; padding: 15px; border-radius: 6px; text-align: center;
        }
        .stat-number { font-size: 2em; font-weight: bold; color: #4ecdc4; }
        .stat-label { color: #b0b0b0; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #3a3a3a; }
        th { background: #3a3a3a; color: #4ecdc4; font-weight: 600; }
        .status-active { color: #4ecdc4; font-weight: bold; }
        .status-inactive { color: #ffa726; font-weight: bold; }
        .status-offline { color: #ff6b6b; font-weight: bold; }
        .btn { 
            background: #4ecdc4; color: #1a1a1a; padding: 8px 16px; 
            border: none; border-radius: 4px; cursor: pointer; font-weight: 600;
        }
        .btn:hover { background: #45b7aa; }
        .btn-danger { background: #ff6b6b; color: white; }
        .btn-danger:hover { background: #ff5252; }
        .command-form { 
            background: #3a3a3a; padding: 20px; border-radius: 6px; margin-top: 20px;
        }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #b0b0b0; }
        .form-group select, .form-group input, .form-group textarea { 
            width: 100%; padding: 8px; background: #2d2d2d; color: #e0e0e0; 
            border: 1px solid #4a4a4a; border-radius: 4px;
        }
        .timestamp { color: #b0b0b0; font-size: 0.9em; }
        .json-data { 
            background: #1a1a1a; padding: 10px; border-radius: 4px; 
            font-family: monospace; font-size: 0.9em; overflow-x: auto;
        }
    </style>
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23ff6b6b'/%3E%3Ccircle cx='32' cy='32' r='20' fill='%231a1a1a'/%3E%3Ccircle cx='32' cy='32' r='8' fill='%23ff6b6b'/%3E%3C/svg%3E">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 RedSignal C2 Dashboard</h1>
            <p>Command and Control Emulation Platform</p>
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/clients">Clients</a>
                <a href="/commands">Commands</a>
            </div>
        </div>
        {content}
    </div>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Command form handling
        function sendCommand() {
            const form = document.getElementById('commandForm');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Parse parameters as JSON if provided
            if (data.parameters) {
                try {
                    data.parameters = JSON.parse(data.parameters);
                } catch (e) {
                    alert('Invalid JSON in parameters field');
                    return;
                }
            } else {
                data.parameters = {};
            }
            
            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                alert('Command sent: ' + result.command_id);
                form.reset();
            })
            .catch(error => {
                alert('Error sending command: ' + error);
            });
        }
    </script>
</body>
</html>
        """

    def render_dashboard(
        self, clients: List[Dict[str, Any]], recent_commands: List[Dict[str, Any]]
    ) -> str:
        """Render the main dashboard page."""

        # Calculate statistics
        total_clients = len(clients)
        active_clients = len([c for c in clients if c["status"] == "active"])
        total_commands = len(recent_commands)

        content = f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_clients}</div>
                <div class="stat-label">Total Clients</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{active_clients}</div>
                <div class="stat-label">Active Clients</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_commands}</div>
                <div class="stat-label">Total Commands</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Recent Clients</h2>
            <table>
                <thead>
                    <tr>
                        <th>Client ID</th>
                        <th>Hostname</th>
                        <th>Platform</th>
                        <th>IP Address</th>
                        <th>Status</th>
                        <th>Last Beacon</th>
                    </tr>
                </thead>
                <tbody>
        """

        for client in clients[:10]:  # Show only recent 10
            last_beacon = datetime.fromtimestamp(client["last_beacon"]).strftime(
                "%H:%M:%S"
            )
            status_class = f"status-{client['status']}"

            content += f"""
                    <tr>
                        <td>{client['client_id'][:16]}...</td>
                        <td>{client['hostname']}</td>
                        <td>{client['platform'][:30]}...</td>
                        <td>{client['ip_address']}</td>
                        <td class="{status_class}">{client['status'].upper()}</td>
                        <td class="timestamp">{last_beacon}</td>
                    </tr>
            """

        content += """
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Recent Commands</h2>
            <table>
                <thead>
                    <tr>
                        <th>Command ID</th>
                        <th>Client</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
        """

        for cmd in recent_commands[:10]:
            created_time = datetime.fromtimestamp(cmd["created_time"]).strftime(
                "%H:%M:%S"
            )
            status_str = cmd["status"]
            # status may be enum or string
            if hasattr(status_str, "value"):
                status_str = status_str.value
            status_class = (
                f"status-{status_str}" if status_str in ["active", "inactive", "offline"] else ""
            )

            content += f"""
                    <tr>
                        <td>{cmd['command_id'][:16]}...</td>
                        <td>{cmd['client_id'][:16]}...</td>
                        <td>{cmd['command_type']}</td>
                        <td class="{status_class}">{status_str.upper()}</td>
                        <td class="timestamp">{created_time}</td>
                    </tr>
            """

        content += """
                </tbody>
            </table>
        </div>
        """

        return self.base_template.format(content=content)

    def render_clients(self, clients: List[Dict[str, Any]]) -> str:
        """Render the clients management page."""

        content = """
        <div class="card">
            <h2>Client Management</h2>
            <table>
                <thead>
                    <tr>
                        <th>Client ID</th>
                        <th>Hostname</th>
                        <th>Platform</th>
                        <th>IP Address</th>
                        <th>Status</th>
                        <th>Beacons</th>
                        <th>Last Beacon</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        """

        for client in clients:
            last_beacon = datetime.fromtimestamp(client["last_beacon"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            status_class = f"status-{client['status']}"

            content += f"""
                    <tr>
                        <td>{client['client_id']}</td>
                        <td>{client['hostname']}</td>
                        <td>{client['platform']}</td>
                        <td>{client['ip_address']}</td>
                        <td class="{status_class}">{client['status'].upper()}</td>
                        <td>{client['beacon_count']}</td>
                        <td class="timestamp">{last_beacon}</td>
                        <td>
                            <button class="btn" onclick="sendQuickCommand('{client['client_id']}', 'collect_system_info')">
                                System Info
                            </button>
                        </td>
                    </tr>
            """

        content += """
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Send Command</h2>
            <form id="commandForm" class="command-form">
                <div class="form-group">
                    <label for="client_id">Client ID:</label>
                    <select name="client_id" required>
                        <option value="">Select Client...</option>
        """

        for client in clients:
            if client["status"] == "active":
                content += f'<option value="{client["client_id"]}">{client["hostname"]} ({client["client_id"][:16]}...)</option>'

        content += """
                    </select>
                </div>
                <div class="form-group">
                    <label for="command_type">Command Type:</label>
                    <select name="command_type" required>
                        <option value="collect_system_info">Collect System Info</option>
                        <option value="list_files">List Files</option>
                        <option value="simulate_exfiltration">Simulate Exfiltration</option>
                        <option value="shell_command">Shell Command</option>
                        <option value="beacon">Beacon</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="parameters">Parameters (JSON):</label>
                    <textarea name="parameters" rows="4" placeholder='{"path": "/tmp", "recursive": false}'></textarea>
                </div>
                <div class="form-group">
                    <label for="timeout">Timeout (seconds):</label>
                    <input type="number" name="timeout" value="30" min="1" max="300">
                </div>
                <button type="button" class="btn" onclick="sendCommand()">Send Command</button>
            </form>
        </div>
        
        <script>
            function sendQuickCommand(clientId, commandType) {
                const data = {
                    client_id: clientId,
                    command_type: commandType,
                    parameters: {},
                    timeout: 30
                };
                
                fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    alert('Command sent: ' + result.command_id);
                })
                .catch(error => {
                    alert('Error: ' + error);
                });
            }
        </script>
        """

        return self.base_template.format(content=content)

    def render_commands(self, commands: List[Dict[str, Any]]) -> str:
        """Render the commands history page."""

        content = """
        <div class="card">
            <h2>Command History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Command ID</th>
                        <th>Client ID</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Execution Time</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        """

        for cmd in commands:
            created_time = datetime.fromtimestamp(cmd["created_time"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            exec_time = (
                f"{cmd['execution_time']:.2f}s" if cmd["execution_time"] else "N/A"
            )
            status_str = cmd["status"]
            if hasattr(status_str, "value"):
                status_str = status_str.value

            content += f"""
                    <tr>
                        <td>{cmd['command_id'][:16]}...</td>
                        <td>{cmd['client_id'][:16]}...</td>
                        <td>{cmd['command_type']}</td>
                        <td>{status_str.upper()}</td>
                        <td class="timestamp">{created_time}</td>
                        <td>{exec_time}</td>
                        <td>
                            <button class="btn" onclick="showCommandDetails('{cmd['command_id']}')">
                                Details
                            </button>
                        </td>
                    </tr>
            """

        content += """
                </tbody>
            </table>
        </div>
        
        <div id="commandDetails" class="card" style="display: none;">
            <h2>Command Details</h2>
            <div id="detailsContent"></div>
        </div>
        
        <script>
            function showCommandDetails(commandId) {
                // This would fetch and display command details
                // For now, just show the command ID
                document.getElementById('commandDetails').style.display = 'block';
                document.getElementById('detailsContent').innerHTML = 
                    '<p>Command ID: ' + commandId + '</p><p>Details would be loaded here...</p>';
            }
        </script>
        """

        return self.base_template.format(content=content)


def create_web_interface() -> WebInterface:
    """Factory function to create web interface instance."""
    return WebInterface()

