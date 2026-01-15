# TARRA - Stop server
import subprocess
import sys
import os

# Try to import psutil, install if missing
try:
    import psutil
except ImportError:
    print("Installation de psutil...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

def stop_server():
    """Stop all running TARRA servers"""
    print("Recherche des serveurs TARRA en cours d'exécution...")
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                # Look for uvicorn process running main:app on port 8000
                if ('uvicorn' in cmdline_str and 'main:app' in cmdline_str) or \
                   ('python' in proc.info['name'].lower() and 'main:app' in cmdline_str):
                    print(f"Arrêt du serveur (PID: {proc.info['pid']})...")
                    proc.kill()
                    proc.wait(timeout=5)
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    
    if killed_count > 0:
        print(f"✓ {killed_count} serveur(s) arrêté(s)")
    else:
        print("Aucun serveur en cours d'exécution")
    
    input("\nAppuyez sur Entrée pour fermer...")

if __name__ == '__main__':
    stop_server()
