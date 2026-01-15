# TARRA - Simple launcher for DICOM Analysis Application
import subprocess
import webbrowser
import time
import sys
import os

def setup_environment():
    """Setup virtual environment and install dependencies if needed"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, 'backend')
    env_dir = os.path.join(backend_dir, 'env')
    python_exe = os.path.join(env_dir, 'Scripts', 'python.exe')
    
    # Check if environment exists
    if not os.path.exists(python_exe):
        print("Première installation... Veuillez patienter...")
        
        # Create virtual environment
        subprocess.run([sys.executable, '-m', 'venv', env_dir], cwd=backend_dir, check=True)
        
        # Upgrade pip
        subprocess.run([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Install requirements
        requirements = os.path.join(backend_dir, 'requirements.txt')
        subprocess.run([python_exe, '-m', 'pip', 'install', '-r', requirements],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Create directories
        os.makedirs(os.path.join(backend_dir, 'data'), exist_ok=True)
        os.makedirs(os.path.join(backend_dir, 'uploads'), exist_ok=True)
        
        print("Installation terminée!")
    
    return backend_dir, python_exe

def start_server_hidden():
    """Start the FastAPI server without showing console"""
    try:
        backend_dir, python_exe = setup_environment()
        
        # Create startup info to hide console (Windows only)
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        else:
            startupinfo = None
            creationflags = 0
        
        # Start server
        process = subprocess.Popen(
            [python_exe, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'],
            cwd=backend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        # Wait for server to be ready
        time.sleep(3)
        
        # Open browser
        webbrowser.open('http://localhost:8000')
        
        return process
        
    except Exception as e:
        print(f"Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == '__main__':
    # Start server
    process = start_server_hidden()
    
    # Keep script running
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
