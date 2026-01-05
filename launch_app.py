# Launcher script - starts the FastAPI server without console window
import subprocess
import webbrowser
import time
import sys
import os

def start_server_hidden():
    """Start the FastAPI server without showing console"""
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, 'backend')
    python_exe = os.path.join(backend_dir, 'env', 'Scripts', 'python.exe')
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Create startup info to hide console (Windows only)
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    else:
        startupinfo = None
    
    # Start server
    process = subprocess.Popen(
        [python_exe, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    
    # Wait for server to be ready
    time.sleep(3)
    
    # Open browser
    webbrowser.open('http://localhost:8000')
    
    return process

if __name__ == '__main__':
    # Start server
    process = start_server_hidden()
    
    # Keep script running
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
