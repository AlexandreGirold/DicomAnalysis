# Guide d'Ajout d'un Nouveau Test

## 1. Créer le Test Python

Créez un fichier dans :
- `backend/services/daily/`
- `backend/services/weekly/`
- `backend/services/monthly/`
- `backend/services/basic_tests/`

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from basic_tests.base_test import BaseTest
from datetime import datetime
from typing import Optional

class MonNouveauTest(BaseTest):
    def __init__(self):
        super().__init__(test_name="Mon Test", description="Description")
    
    def execute(self, operator: str, param1: float, test_date: Optional[datetime] = None, notes: Optional[str] = None):
        self.set_test_info(operator, test_date)
        self.add_input("operator", operator, "text")
        self.add_input("param1", param1, "mm")
        
        result = param1 * 2
        status = "PASS" if result < 10 else "FAIL"
        self.add_result(name="check1", value=result, status=status, unit="mm", tolerance="< 10 mm")
        
        self.calculate_overall_result()
        return self.to_dict()
    
    def get_form_data(self):
        return {
            'title': 'Mon Test',
            'fields': [
                {'name': 'test_date', 'label': 'Date:', 'type': 'date', 'required': True},
                {'name': 'operator', 'label': 'Opérateur:', 'type': 'text', 'required': True},
                {'name': 'param1', 'label': 'Paramètre (mm):', 'type': 'number', 'required': True, 'step': '0.01'}
            ],
            'category': 'daily'
        }

def test_mon_nouveau_test(operator: str, param1: float, test_date: Optional[datetime] = None, notes: Optional[str] = None):
    return MonNouveauTest().execute(operator, param1, test_date, notes)
```



## 2. Enregistrer dans `__init__.py`

Dans `backend/services/daily/__init__.py` :
```python
from services.daily.mon_nouveau_test import MonNouveauTest, test_mon_nouveau_test

DAILY_TESTS = {
    'mon_nouveau_test': {
        'class': MonNouveauTest,
        'function': test_mon_nouveau_test,
        'description': 'Description',
        'category': 'daily'
    }
}
```

## 3. API Endpoint (optionnel)

Dans `backend/main.py` :
```python
@app.post("/basic-tests/mon-nouveau-test")
async def execute_mon_nouveau_test(data: dict):
    from services.daily.mon_nouveau_test import MonNouveauTest
    test = MonNouveauTest()
    return JSONResponse(test.execute(**data))
```

## 4. Frontend - Automatique

Le frontend génère automatiquement le formulaire via `get_form_data()`. Aucune modification nécessaire.

## 5. Tester

```powershell
cd backend
.\env\Scripts\python.exe test_imports.py
```

Ouvrez `http://localhost:8000` et testez dans le navigateur.
