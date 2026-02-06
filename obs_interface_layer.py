"""
OBS Football Shortcut Client
A system tray application that receives OBS commands from the server
and simulates keyboard key presses for OBS hotkey integration.
"""

# REQUEST ADMIN PRIVILEGE FOR KEY EMULATION

import sys
import ctypes

def request_admin_privileges():
    """Request administrator privileges on Windows."""
    if sys.platform != 'win32':
        return True
    
    try:
        # Check if already running as admin
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False
    
    # Not admin, re-run with elevated privileges
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas",                          # Operation: "runas" = run as admin
            sys.executable,                   # Python executable
            " ".join(sys.argv),               # Script arguments
            None,                             # Working directory
            1                                 # Show window (SW_SHOW)
        )
        sys.exit(0)  # Exit current (non-admin) process
    except Exception as e:
        logger.error(f"Failed to request admin privileges: {e}")
        return False



# APP CODE

import pystray
from PIL import Image
import socketio
import requests
import threading
import sys
import os
import time
import json
import logging
from pathlib import Path

# Platform-specific imports
if sys.platform == 'win32':
    import keyboard
    import ctypes
else:
    print("Warning: Keyboard simulation requires Windows")
    keyboard = None


from config import PORT


# ===========================
# Configuration
# ===========================

CONFIG_FILE = "shortcut_client_config.json"
LOG_FILE = "shortcut_client.log"
SERVER_PORT = PORT
SERVER_URL = f"http://localhost:{SERVER_PORT}"

DEFAULT_CONFIG = {
    "server_url": SERVER_URL,
}

# ===========================
# Logging Setup
# ===========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ShortcutClient:
    """System tray application for OBS command execution."""

    def __init__(self):
        self.config = self.load_config()
        self.server_url = self.config.get("server_url", SERVER_URL)

        self.connected = False
        self.obs_commands = []
        self.console_visible = False
        self.running = True
        self.icon = None
        self.connection_thread = None

        # SocketIO client with auto-reconnection
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1,
            reconnection_delay_max=10,
            logger=False,
            engineio_logger=False
        )

        self.setup_socketio_handlers()

        # Hide console on startup
        if sys.platform == 'win32':
            self.hide_console()

    # ===========================
    # Configuration Management
    # ===========================

    def load_config(self):
        """Load configuration from file or create default."""
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded from {CONFIG_FILE}")
                    return {**DEFAULT_CONFIG, **config}
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save configuration to file."""
        try:
            config_data = {"server_url": self.server_url}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    # ===========================
    # Console Visibility (Windows)
    # ===========================

    def hide_console(self):
        """Hide the console window."""
        if sys.platform != 'win32':
            return
        try:
            hwnd = ctypes.WinDLL('kernel32').GetConsoleWindow()
            if hwnd:
                ctypes.WinDLL('user32').ShowWindow(hwnd, 0)
                self.console_visible = False
                logger.info("Console hidden")
        except Exception as e:
            logger.error(f"Error hiding console: {e}")

    def show_console(self):
        """Show the console window."""
        if sys.platform != 'win32':
            return
        try:
            hwnd = ctypes.WinDLL('kernel32').GetConsoleWindow()
            if hwnd:
                user32 = ctypes.WinDLL('user32')
                user32.ShowWindow(hwnd, 5)
                user32.SetForegroundWindow(hwnd)
                self.console_visible = True
                logger.info("Console shown")
        except Exception as e:
            logger.error(f"Error showing console: {e}")

    def toggle_console(self, icon=None, item=None):
        """Toggle console visibility."""
        if self.console_visible:
            self.hide_console()
        else:
            self.show_console()
        self.update_menu()

    # ===========================
    # SocketIO Setup
    # ===========================

    def setup_socketio_handlers(self):
        """Setup SocketIO event handlers."""

        @self.sio.event
        def connect():
            self.connected = True
            logger.info(f"Connected to server")
            self.update_icon()

        @self.sio.event
        def disconnect():
            self.connected = False
            logger.warning("Disconnected from server")
            self.update_icon()

        @self.sio.event
        def connect_error(data):
            self.connected = False
            logger.error(f"Connection error: {data}")
            self.update_icon()

        @self.sio.on('execute-obs-command')
        def on_execute_obs_command(data):
            """Receive command execution request from server."""
            start_time = time.time()
            command_id = data.get('id')
            shortcut = data.get('shortcut')
            command_name = data.get('name', 'Unknown')

            logger.info(
                f"Received command: {command_name} "
                f"(ID: {command_id}, Shortcut: {shortcut})"
            )
            self.simulate_keypress(shortcut)
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Command executed in {elapsed:.1f}ms")

        @self.sio.on('update-obs-commands')
        def on_update_obs_commands():
            """Refresh OBS commands list from server."""
            logger.info("OBS commands updated, refreshing...")
            self.fetch_obs_commands()

    # ===========================
    # Server Communication
    # ===========================

    def connect_to_server(self):
        """Connect to the SocketIO server."""
        if self.sio.connected:
            return True

        try:
            logger.info(f"Connecting to {self.server_url}...")
            self.sio.connect(
                self.server_url,
                transports=['websocket', 'polling']
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            self.update_icon()
            return False

    def disconnect_from_server(self):
        """Disconnect from the server."""
        try:
            if self.sio.connected:
                self.sio.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def fetch_obs_commands(self):
        """Fetch OBS commands from the server."""
        try:
            response = requests.get(
                f"{self.server_url}/obs-commands",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.obs_commands = data.get('obs_commands', [])
                logger.info(f"Fetched {len(self.obs_commands)} OBS commands")
                self.update_menu()
                return True
            else:
                logger.error(
                    f"Failed to fetch commands: HTTP {response.status_code}"
                )
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching commands: {e}")
            return False

    # ===========================
    # Keyboard Simulation
    # ===========================

    def simulate_keypress(self, shortcut):
        """Simulate a key press for the given shortcut."""
        if not shortcut:
            logger.warning("No shortcut provided")
            return

        if sys.platform != 'win32' or keyboard is None:
            logger.warning(
                f"Keyboard simulation not available. Would press: {shortcut}"
            )
            return

        try:
            key = shortcut.lower()
            keyboard.press_and_release(key)
            logger.info(f"Simulated key press: {shortcut}")
        except Exception as e:
            logger.error(f"Error simulating key press '{shortcut}': {e}")

    # ===========================
    # System Tray Icon
    # ===========================

    def update_icon(self):
        """Update the tray icon based on connection status."""
        if self.icon:
            icon_file = "connected.ico" if self.connected else "disconnected.ico"
            try:
                self.icon.icon = Image.open(icon_file)
            except Exception as e:
                logger.error(f"Error loading icon {icon_file}: {e}")
            self.update_tooltip()

    def update_tooltip(self):
        """Update the icon tooltip."""
        if self.icon:
            status = "Connected" if self.connected else "Disconnected"
            self.icon.title = (
                f"OBS Football Client\n"
                f"Status: {status}\n"
                f"Server: {self.server_url}"
            )

    def update_menu(self):
        """Rebuild and update the tray menu."""
        if self.icon:
            self.icon.menu = self.build_menu()
            self.update_tooltip()

    def build_menu(self):
        """Build the system tray context menu."""
        menu_items = []

        # Status header
        status_text = "● Connected" if self.connected else "○ Disconnected"
        menu_items.append(pystray.MenuItem(status_text, None, enabled=False))
        menu_items.append(pystray.Menu.SEPARATOR)

        # Refresh commands
        menu_items.append(pystray.MenuItem(
            "Refresh Commands",
            self.on_refresh_commands
        ))

        menu_items.append(pystray.Menu.SEPARATOR)

        # OBS Commands submenu
        if self.obs_commands:
            command_items = []
            for cmd in self.obs_commands:
                command_items.append(pystray.MenuItem(
                    f"{cmd['name']} ({cmd.get('shortcut', 'N/A')})",
                    self.make_command_handler(cmd),
                    enabled=self.connected
                ))

            menu_items.append(pystray.MenuItem(
                "Manual Trigger",
                pystray.Menu(*command_items)
            ))
        else:
            menu_items.append(pystray.MenuItem(
                "No commands available",
                None,
                enabled=False
            ))

        menu_items.append(pystray.Menu.SEPARATOR)

        # Console toggle
        console_text = (
            "Hide Console" if self.console_visible else "Show Console"
        )
        menu_items.append(pystray.MenuItem(console_text, self.toggle_console))

        menu_items.append(pystray.Menu.SEPARATOR)

        # Quit
        menu_items.append(pystray.MenuItem("Quit", self.on_quit))

        return pystray.Menu(*menu_items)

    def make_command_handler(self, cmd):
        """Create a handler for command execution."""
        def handler(icon=None, item=None):
            self.execute_command(cmd['id'])
        return handler

    def execute_command(self, command_id):
        """Emit command execution request to server."""
        try:
            self.sio.emit('trigger-obs-command', {'id': command_id})
            logger.info(f"Triggered command ID: {command_id}")
        except Exception as e:
            logger.error(f"Error executing command: {e}")

    # ===========================
    # Menu Action Handlers
    # ===========================

    def on_refresh_commands(self, icon=None, item=None):
        """Handle refresh commands menu click."""
        logger.info("Refreshing commands...")

        if not self.connected:
            self.connect_to_server()

        self.fetch_obs_commands()

    def on_quit(self, icon=None, item=None):
        """Handle quit menu click."""
        logger.info("Shutting down...")
        self.running = False
        self.disconnect_from_server()
        if self.icon:
            self.icon.stop()

    # ===========================
    # Main Run Loop
    # ===========================

    def background_tasks(self):
        """Background thread for connection management."""
        # Initial connection
        time.sleep(1)
        self.connect_to_server()
        self.fetch_obs_commands()

        # Keep-alive and reconnection loop
        while self.running:
            time.sleep(5)

            if not self.connected and self.running:
                logger.info("Attempting to reconnect...")
                self.connect_to_server()
                if self.connected:
                    self.fetch_obs_commands()

    def run(self):
        """Run the application."""
        logger.info("Starting OBS Football Shortcut Client...")
        logger.info(f"Server URL: {self.server_url}")

        # Create the system tray icon
        try:
            self.icon = pystray.Icon(
                name="OBS Football Client",
                icon=Image.open("disconnected.ico"),
                title="OBS Football Client\nStatus: Disconnected",
                menu=self.build_menu()
            )
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            logger.info("Running without system tray")
            self.icon = None

        # Start background thread
        self.connection_thread = threading.Thread(
            target=self.background_tasks,
            daemon=True
        )
        self.connection_thread.start()

        # Run icon if available
        if self.icon:
            self.icon.run()
        else:
            # Fallback: keep application running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.on_quit()

        logger.info("OBS Football Client stopped")


def main():
    """Main entry point."""

    if not request_admin_privileges():
        print("ERROR: This application requires administrator privileges")
        print("Please run as Administrator or grant privileges when prompted")
        sys.exit(1)

    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("OBS Football Shortcut Client")
            print("\nUsage: python shortcut_client.py [options]")
            print("\nOptions:")
            print("  -h, --help     Show this help message")
            print("\nConfiguration is stored in shortcut_client_config.json")
            return

    try:
        client = ShortcutClient()
        client.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()