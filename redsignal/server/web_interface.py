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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a; color: #e0e0e0; line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: #2d2d2d; padding: 20px; border-radius: 8px; 
            margin-bottom: 30px; border-left: 4px solid #ff6b6b;
        }}
        .nav {{ display: flex; gap: 20px; margin-top: 15px; }}
        .nav a {{ 
            color: #4ecdc4; text-decoration: none; padding: 8px 16px;
            border-radius: 4px; transition: background 0.3s;
        }}
        .nav a:hover {{ background: #3a3a3a; }}
        .card {{ 
            background: #2d2d2d; padding: 20px; border-radius: 8px; 
            margin-bottom: 20px; border-left: 4px solid #4ecdc4;
        }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-card {{ 
            background: #3a3a3a; padding: 15px; border-radius: 6px; text-align: center;
        }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #4ecdc4; }}
        .stat-label {{ color: #b0b0b0; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #3a3a3a; }}
        th {{ background: #3a3a3a; color: #4ecdc4; font-weight: 600; }}
        .status-active {{ color: #4ecdc4; font-weight: bold; }}
        .status-inactive {{ color: #ffa726; font-weight: bold; }}
        .status-offline {{ color: #ff6b6b; font-weight: bold; }}
        .status-completed {{ color: #4caf50; font-weight: bold; }}
        .status-failed {{ color: #ff6b6b; font-weight: bold; }}
        .status-queued {{ color: #ffa726; font-weight: bold; }}
        .status-dispatched {{ color: #2196f3; font-weight: bold; }}
        .btn {{ 
            background: #4ecdc4; color: #1a1a1a; padding: 8px 16px; 
            border: none; border-radius: 4px; cursor: pointer; font-weight: 600;
            margin: 2px;
        }}
        .btn:hover {{ background: #45b7aa; }}
        .btn-danger {{ background: #ff6b6b; color: white; }}
        .btn-danger:hover {{ background: #ff5252; }}
        .btn-small {{ padding: 4px 8px; font-size: 0.8em; }}
        .command-form {{ 
            background: #3a3a3a; padding: 20px; border-radius: 6px; margin-top: 20px;
        }}
        .form-group {{ margin-bottom: 15px; }}
        .form-group label {{ display: block; margin-bottom: 5px; color: #b0b0b0; }}
        .form-group select, .form-group input, .form-group textarea {{ 
            width: 100%; padding: 8px; background: #2d2d2d; color: #e0e0e0; 
            border: 1px solid #4a4a4a; border-radius: 4px;
        }}
        .timestamp {{ color: #b0b0b0; font-size: 0.9em; }}
        .json-data {{ 
            background: #1a1a1a; padding: 15px; border-radius: 4px; 
            font-family: 'Courier New', monospace; font-size: 0.9em; overflow-x: auto;
            border: 1px solid #3a3a3a; white-space: pre-wrap;
        }}
        
        /* Modal Styles */
        .modal {{
            display: none; position: fixed; z-index: 1000; left: 0; top: 0;
            width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.8);
        }}
        .modal-content {{
            background-color: #2d2d2d; margin: 5% auto; padding: 0;
            border-radius: 8px; width: 90%; max-width: 900px; max-height: 80vh;
            overflow: hidden; border: 1px solid #4a4a4a;
        }}
        .modal-header {{
            background: #3a3a3a; color: #e0e0e0; padding: 20px;
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #4a4a4a;
        }}
        .modal-header h2 {{ margin: 0; color: #4ecdc4; }}
        .close {{
            color: #b0b0b0; font-size: 28px; font-weight: bold;
            cursor: pointer; transition: color 0.3s;
        }}
        .close:hover {{ color: #ff6b6b; }}
        .modal-body {{
            padding: 20px; max-height: 60vh; overflow-y: auto;
            background: #2d2d2d;
        }}
        
        /* Command Details Styling */
        .details-section {{
            margin-bottom: 25px; padding: 15px; background: #3a3a3a;
            border-radius: 6px; border-left: 4px solid #4ecdc4;
        }}
        .details-section h4 {{
            margin: 0 0 15px 0; color: #4ecdc4; font-size: 16px;
        }}
        .details-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        .detail-item {{
            display: flex; flex-direction: column;
        }}
        .detail-item label {{
            font-weight: bold; color: #b0b0b0; font-size: 12px;
            margin-bottom: 4px; text-transform: uppercase;
        }}
        .detail-item span {{
            color: #e0e0e0; font-family: 'Courier New', monospace;
            background: #1a1a1a; padding: 8px; border-radius: 4px;
            border: 1px solid #4a4a4a; word-break: break-all;
        }}
        .status-badge {{
            display: inline-block; padding: 4px 12px; border-radius: 12px;
            font-size: 12px; font-weight: bold; text-transform: uppercase;
        }}
        .status-badge.completed {{ background: #4caf50; color: white; }}
        .status-badge.failed {{ background: #ff6b6b; color: white; }}
        .status-badge.queued {{ background: #ffa726; color: white; }}
        .status-badge.dispatched {{ background: #2196f3; color: white; }}
        
        /* Error section */
        .error-section {{
            border-left-color: #ff6b6b !important; background: #4a2c2c !important;
        }}
        .error-message {{
            background: #1a1a1a; padding: 12px; border-radius: 4px;
            border: 1px solid #ff6b6b; color: #ff6b6b;
            font-family: 'Courier New', monospace;
        }}
        
        /* Loading spinner */
        .loading {{
            text-align: center; padding: 40px;
        }}
        .spinner {{
            border: 4px solid #3a3a3a; border-top: 4px solid #4ecdc4;
            border-radius: 50%; width: 40px; height: 40px;
            animation: spin 1s linear infinite; margin: 0 auto 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Notifications */
        .notification {{
            position: fixed; top: 20px; right: 20px; padding: 12px 20px;
            border-radius: 4px; color: white; font-weight: bold; z-index: 10000;
            animation: slideIn 0.3s ease-out;
        }}
        .notification.success {{ background: #4caf50; }}
        .notification.error {{ background: #ff6b6b; }}
        .notification.info {{ background: #2196f3; }}
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        /* Action buttons */
        .action-buttons {{
            display: flex; gap: 10px; justify-content: center;
            margin-top: 20px; padding-top: 20px;
            border-top: 1px solid #4a4a4a;
        }}
    </style>
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
    
    <!-- Command Details Modal -->
    <div id="commandModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Command Details</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div id="detailsContent">
                    <!-- Command details will be loaded here -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Command form handling
        function sendCommand() {{
            const form = document.getElementById('commandForm');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Parse parameters as JSON if provided
            if (data.parameters) {{
                try {{
                    data.parameters = JSON.parse(data.parameters);
                }} catch (e) {{
                    showNotification('Invalid JSON in parameters field', 'error');
                    return;
                }}
            }} else {{
                data.parameters = {{}};
            }}
            
            fetch('/api/command', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.status === 'queued') {{
                    showNotification('Command sent: ' + result.command_id.substring(0, 8) + '...', 'success');
                    form.reset();
                }} else {{
                    showNotification('Failed to send command', 'error');
                }}
            }})
            .catch(error => {{
                showNotification('Error sending command: ' + error, 'error');
            }});
        }}
        
        // Quick command function
        function sendQuickCommand(clientId, commandType) {{
            const data = {{
                client_id: clientId,
                command_type: commandType,
                parameters: {{}},
                timeout: 30
            }};
            
            fetch('/api/command', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.status === 'queued') {{
                    showNotification('Command sent: ' + result.command_id.substring(0, 8) + '...', 'success');
                }} else {{
                    showNotification('Failed to send command', 'error');
                }}
            }})
            .catch(error => {{
                showNotification('Error: ' + error, 'error');
            }});
        }}
        
        // Show command details modal - DEBUG VERSION
        async function showCommandDetails(commandId) {{
            const modal = document.getElementById('commandModal');
            const detailsContent = document.getElementById('detailsContent');
            
            console.log('Fetching details for command:', commandId); // DEBUG
            
            // Show loading state
            detailsContent.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading command details...</p>
                </div>
            `;
            
            // Show modal
            modal.style.display = 'block';
            
            try {{
                // Fetch command details from your API
                const url = '/api/command/' + commandId;
                console.log('Fetching from URL:', url); // DEBUG
                
                const response = await fetch(url);
                console.log('Response status:', response.status); // DEBUG
                
                const result = await response.json();
                console.log('Response data:', result); // DEBUG
                
                if (result.success) {{
                    const command = result.data;
                    
                    // Format timestamps
                    const createdAt = command.created_time ? new Date(command.created_time * 1000).toLocaleString() : 'N/A';
                    const dispatchedAt = command.dispatched_time ? new Date(command.dispatched_time * 1000).toLocaleString() : 'N/A';
                    const completedAt = command.completed_time ? new Date(command.completed_time * 1000).toLocaleString() : 'N/A';
                    const executionTime = command.execution_time ? command.execution_time.toFixed(2) + 's' : 'N/A';
                    
                    // Build the details HTML
                    let html = `
                        <div class="details-section">
                            <h4>📋 Basic Information</h4>
                            <div class="details-grid">
                                <div class="detail-item">
                                    <label>Command ID</label>
                                    <span>${{command.command_id}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Client ID</label>
                                    <span>${{command.client_id}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Command Type</label>
                                    <span>${{command.command_type}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Status</label>
                                    <span class="status-badge ${{command.status}}">${{command.status.toUpperCase()}}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="details-section">
                            <h4>⏱️ Timing Information</h4>
                            <div class="details-grid">
                                <div class="detail-item">
                                    <label>Created At</label>
                                    <span>${{createdAt}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Dispatched At</label>
                                    <span>${{dispatchedAt}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Completed At</label>
                                    <span>${{completedAt}}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Execution Time</label>
                                    <span>${{executionTime}}</span>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Add parameters section if exists
                    if (command.parameters && Object.keys(command.parameters).length > 0) {{
                        html += `
                            <div class="details-section">
                                <h4>⚙️ Parameters</h4>
                                <div class="json-data">${{JSON.stringify(command.parameters, null, 2)}}</div>
                            </div>
                        `;
                    }}
                    
                    // Add response data section if exists
                    if (command.response_data) {{
                        html += `
                            <div class="details-section">
                                <h4>📤 Response Data</h4>
                                <div class="json-data">${{JSON.stringify(command.response_data, null, 2)}}</div>
                            </div>
                        `;
                    }}
                    
                    // Add error section if exists
                    if (command.error_message) {{
                        html += `
                            <div class="details-section error-section">
                                <h4>❌ Error Information</h4>
                                <div class="error-message">${{command.error_message}}</div>
                            </div>
                        `;
                    }}
                    
                    // Add action buttons
                    html += `
                        <div class="action-buttons">
                            <button class="btn" onclick="copyToClipboard('${{command.command_id}}')">
                                📋 Copy Command ID
                            </button>
                            <button class="btn" onclick="closeModal()">
                                ✖️ Close
                            </button>
                        </div>
                    `;
                    
                    detailsContent.innerHTML = html;
                    
                }} else {{
                    detailsContent.innerHTML = `
                        <div class="error-section">
                            <h4>❌ Error Loading Command Details</h4>
                            <p>${{result.error || 'Could not fetch command details. Please try again.'}}</p>
                            <p><strong>Debug info:</strong> Response success = false</p>
                        </div>
                    `;
                }}
                
            }} catch (error) {{
                console.error('Error fetching command details:', error);
                detailsContent.innerHTML = `
                    <div class="error-section">
                        <h4>❌ Network Error</h4>
                        <p>Failed to load command details. Check your connection and try again.</p>
                        <p><strong>Error:</strong> ${{error.message}}</p>
                    </div>
                `;
            }}
        }}
        
        // Close modal
        function closeModal() {{
            document.getElementById('commandModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('commandModal');
            if (event.target === modal) {{
                modal.style.display = 'none';
            }}
        }}
        
        // Copy to clipboard
        async function copyToClipboard(text) {{
            try {{
                await navigator.clipboard.writeText(text);
                showNotification('Copied to clipboard!', 'success');
            }} catch (error) {{
                showNotification('Failed to copy to clipboard', 'error');
            }}
        }}
        
        // Show notification
        function showNotification(message, type = 'info') {{
            // Remove existing notifications
            const existingNotifications = document.querySelectorAll('.notification');
            existingNotifications.forEach(notification => notification.remove());
            
            // Create new notification
            const notification = document.createElement('div');
            notification.className = 'notification ' + type;
            notification.textContent = message;
            
            // Add to page
            document.body.appendChild(notification);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, 3000);
        }}
        
        // Handle escape key to close modal
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
        """
    
    def render_dashboard(self, clients: List[Dict[str, Any]], recent_commands: List[Dict[str, Any]]) -> str:
        """Render the main dashboard page."""
        
        # Calculate statistics
        total_clients = len(clients)
        active_clients = len([c for c in clients if c['status'] == 'active'])
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
            last_beacon = datetime.fromtimestamp(client['last_beacon']).strftime('%H:%M:%S')
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
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for cmd in recent_commands[:10]:
            created_time = datetime.fromtimestamp(cmd['created_time']).strftime('%H:%M:%S')
            status_class = f"status-{cmd['status']}"
            
            content += f"""
                    <tr>
                        <td>{cmd['command_id'][:16]}...</td>
                        <td>{cmd['client_id'][:16]}...</td>
                        <td>{cmd['command_type']}</td>
                        <td class="{status_class}">{cmd['status'].upper()}</td>
                        <td class="timestamp">{created_time}</td>
                        <td>
                            <button class="btn btn-small" onclick="showCommandDetails('{cmd['command_id']}')">
                                Details
                            </button>
                        </td>
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
            last_beacon = datetime.fromtimestamp(client['last_beacon']).strftime('%Y-%m-%d %H:%M:%S')
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
                            <button class="btn btn-small" onclick="sendQuickCommand('{client['client_id']}', 'collect_system_info')">
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
            if client['status'] == 'active':
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
            created_time = datetime.fromtimestamp(cmd['created_time']).strftime('%Y-%m-%d %H:%M:%S')
            exec_time = f"{cmd['execution_time']:.2f}s" if cmd['execution_time'] else "N/A"
            status_class = f"status-{cmd['status']}"
            
            content += f"""
                    <tr>
                        <td>{cmd['command_id'][:16]}...</td>
                        <td>{cmd['client_id'][:16]}...</td>
                        <td>{cmd['command_type']}</td>
                        <td class="{status_class}">{cmd['status'].upper()}</td>
                        <td class="timestamp">{created_time}</td>
                        <td>{exec_time}</td>
                        <td>
                            <button class="btn btn-small" onclick="showCommandDetails('{cmd['command_id']}')">
                                Details
                            </button>
                        </td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        """
        
        return self.base_template.format(content=content)

def create_web_interface() -> WebInterface:
    """Factory function to create web interface instance."""
    return WebInterface()