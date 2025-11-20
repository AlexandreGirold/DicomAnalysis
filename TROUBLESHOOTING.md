# 🔧 Troubleshooting Guide

## Problem: "Only HTML works, backend not connecting"

### Quick Fix Steps:

1. **Stop any running servers**
   - Press `Ctrl+C` in any open command windows
   - Close all browser tabs of the application

2. **Double-click `start_app.bat`**
   - Wait for the message "Application startup complete"
   - Browser should open automatically to `http://localhost:8000`

3. **Test the connection**
   - Open: `http://localhost:8000/TEST_CONNECTION.html`
   - This will run automatic tests
   - All tests should show ✅

### Detailed Troubleshooting:

#### Issue: "Server won't start"

**Check 1: Virtual environment**
```bash
cd backend
dir env\Scripts\python.exe
```
If not found, create it:
```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

**Check 2: Port 8000 in use**
```bash
netstat -ano | findstr :8000
```
If something is using port 8000, kill it or change the port in `start_app.bat`

**Check 3: Dependencies**
```bash
cd backend
env\Scripts\python.exe -m pip list
```
Should show: fastapi, uvicorn, pydicom, sqlalchemy, etc.

#### Issue: "Browser shows error"

**Check browser console (F12)**
- Look for CORS errors → Server not running
- Look for 404 errors → Check API endpoints
- Look for network errors → Server crashed

**Common errors:**

1. **"Failed to fetch"**
   - Server not running
   - Solution: Run `start_app.bat`

2. **"CORS policy"**
   - Opening HTML file directly (file://)
   - Solution: Access via http://localhost:8000

3. **"404 Not Found"**
   - API endpoint doesn't exist
   - Solution: Check main.py has all endpoints

#### Issue: "Database errors"

**Reset database:**
```bash
cd backend\data
del mlc_analysis.db
```
Then restart the server - database will be recreated automatically.

### Manual Start (if batch file doesn't work):

```bash
# Open PowerShell
cd C:\Users\agirold\Desktop\DicomAnalysis\backend

# Activate environment
.\env\Scripts\Activate.ps1

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open browser to: http://localhost:8000

### Verification Checklist:

- [ ] Virtual environment exists: `backend\env\Scripts\python.exe`
- [ ] Dependencies installed: `pip list` shows fastapi, uvicorn
- [ ] Server starts without errors
- [ ] Browser opens to `http://localhost:8000` (not file://)
- [ ] Main page loads (HTML visible)
- [ ] API responds: `http://localhost:8000/database/stats` shows JSON
- [ ] No CORS errors in browser console (F12)

### Still Not Working?

1. **Check the server output**
   - Look for error messages in the command window
   - Common issues: import errors, missing modules

2. **Test API directly**
   ```bash
   # In another PowerShell window
   curl http://localhost:8000/database/stats
   ```
   Should return JSON data

3. **Check firewall**
   - Windows Firewall might block port 8000
   - Allow Python through firewall

4. **Use the test page**
   - Open: `http://localhost:8000/TEST_CONNECTION.html`
   - Run automatic diagnostics

### Need More Help?

**Collect this info:**
1. Output from `start_app.bat`
2. Browser console errors (F12 → Console tab)
3. Python version: `python --version`
4. OS version: `winver`

---

## Quick Commands Reference

**Start server:**
```bash
start_app.bat
```

**Stop server:**
```
Press Ctrl+C in the server window
```

**Reset database:**
```bash
cd backend\data
del mlc_analysis.db
```

**Reinstall dependencies:**
```bash
cd backend
env\Scripts\activate
pip install -r requirements.txt --upgrade
```

**Check if server is running:**
```bash
netstat -ano | findstr :8000
```
