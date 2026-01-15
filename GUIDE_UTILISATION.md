# Comment utiliser TARRA

## 🚀 Démarrer l'application

**Double-cliquez sur `launch_app.py`**

Cela va:
- ✓ Vérifier et arrêter tout serveur existant
- ✓ Démarrer un nouveau serveur avec auto-reload (redémarre automatiquement lors de modifications du code)
- ✓ Ouvrir votre navigateur sur http://localhost:8000
- ✓ Afficher une console séparée avec les logs du serveur

La fenêtre de lancement se fermera automatiquement après 3 secondes.

## 🔄 Redémarrer l'application

**Pour voir vos modifications:**

### Méthode 1: Auto-reload (Recommandé)
Le serveur redémarre **automatiquement** quand vous modifiez des fichiers Python.
- Sauvegardez votre fichier
- Attendez 2-3 secondes
- Rafraîchissez la page du navigateur (F5)

### Méthode 2: Redémarrage manuel
Si l'auto-reload ne fonctionne pas:
1. Double-cliquez sur `launch_app.py` à nouveau
   - Il arrêtera automatiquement l'ancien serveur
   - Démarrera un nouveau serveur
   - Ouvrira un nouvel onglet

## 🛑 Arrêter l'application

### Méthode 1: Fermer la console (Simple)
- Fermez la fenêtre noire de la console du serveur
- Ou appuyez sur Ctrl+C dans la console

### Méthode 2: Script d'arrêt
**Double-cliquez sur `stop_app.py`**
- Arrête tous les serveurs TARRA en cours

## 🔍 Vérifier si le serveur fonctionne

Ouvrez votre navigateur et allez sur:
- http://localhost:8000

Si la page charge, le serveur fonctionne! ✓

## ⚠️ Problèmes courants

### Le serveur ne démarre pas
```powershell
# Dans PowerShell, tuez tous les processus Python:
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Puis relancez launch_app.py
```

### Port 8000 déjà utilisé
Le script `launch_app.py` détecte et arrête automatiquement les serveurs existants.
Si le problème persiste, utilisez `stop_app.py` d'abord.

### Les modifications ne sont pas visibles
1. Vérifiez que vous avez **sauvegardé** le fichier
2. Regardez la console du serveur - elle devrait afficher "Reloading..."
3. Rafraîchissez le navigateur (F5) ou faites Ctrl+Shift+R (rafraîchissement forcé)
4. Si rien ne fonctionne, relancez `launch_app.py`

## 📝 Workflow de développement recommandé

1. **Lancez une fois**: `launch_app.py`
2. **Développez**: Modifiez vos fichiers Python
3. **Testez**: Sauvegardez + attendez 2-3s + rafraîchissez le navigateur
4. **Répétez**: L'auto-reload s'occupe du reste!

Quand vous avez terminé:
- Fermez la console du serveur
- Ou lancez `stop_app.py`

## 🔧 Options avancées

### Lancer manuellement avec auto-reload
```powershell
cd backend
.\env\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Voir les logs en direct
La console du serveur affiche:
- Les requêtes HTTP
- Les erreurs
- Les messages de redémarrage
- Les logs de votre application
