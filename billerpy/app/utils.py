import sys
import os

def get_path(relative_path: str) -> str:
    """Get absolute path to bundled resource (templates, bundled static)"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Fallback to local project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

def get_persistent_path(relative_path: str = "") -> str:
    """Get absolute path to persistent data (DB, user uploads), next to the EXE/Script"""
    if getattr(sys, 'frozen', False):
        # Running as EXE - use EXE location
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as Script - use project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    final_path = os.path.join(base_path, relative_path)
    # Ensure directory exists if we're asking for a folder
    if not os.path.splitext(final_path)[1]: 
        os.makedirs(final_path, exist_ok=True)
        
    return final_path

def get_data_path(filename: str) -> str:
    """Backward compatibility for DB filename"""
    return get_persistent_path(filename)

def get_services():
    services = []
    try:
        if getattr(sys, 'frozen', False):
            # In frozen mode, look in the bundled temporary folder
            base_path = sys._MEIPASS
            file_path = os.path.join(base_path, "assets", "OUR SERVICES.txt")
            
            # Fallback to local file if bundled one not found (rare, but good for sidecar)
            if not os.path.exists(file_path):
                 base_dir = os.path.dirname(sys.executable)
                 file_path = os.path.join(base_dir, "assets", "OUR SERVICES.txt")
        else:
            # Development mode
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(os.path.dirname(base_dir), "assets", "OUR SERVICES.txt")
            
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('•') or line.startswith('•'): 
                        service = line[1:].strip()
                        if service:
                            services.append(service)
    except Exception as e:
        print(f"Error reading services: {e}")
    return services
