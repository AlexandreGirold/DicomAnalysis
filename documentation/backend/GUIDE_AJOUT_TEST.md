# Guide: Ajouter un Nouveau Test

Guide simplifié pour ajouter un nouveau type de test à la base de données.

## Structure de la Base de Données

Les tests sont organisés par fréquence dans `backend/database/`:
- **daily_tests.py** - Tests quotidiens
- **weekly_tests.py** - Tests hebdomadaires  
- **monthly_tests.py** - Tests mensuels

## Étapes Simplifiées

### 1. Ajouter le Modèle de Données

Ouvrir le fichier approprié (`daily_tests.py`, `weekly_tests.py`, ou `monthly_tests.py`) et ajouter votre modèle :

```python
class MyNewTest(Base):
    """Description du test"""
    __tablename__ = "weekly_my_new_test"
    
    # Champs obligatoires (NE PAS MODIFIER)
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    
    # VOS CHAMPS SPÉCIFIQUES ICI
    measurement_1 = Column(Float, nullable=False)
    measurement_2 = Column(String, nullable=True)
```

### 2. Exporter le Modèle

Dans le même fichier, ajouter à la fin :

```python
__all__ = ['MyNewTest', ...]  # Ajouter votre classe
```

Puis dans `backend/database/__init__.py`, importer :

```python
from .weekly_tests import MyNewTest
```

### 3. Ajouter la Fonction de Sauvegarde

Dans `backend/database_helpers.py`, ajouter :

```python
def save_my_new_test(test_date, operator, measurement_1, overall_result, **kwargs):
    """Sauvegarde un nouveau test"""
    db = SessionLocal()
    try:
        test = MyNewTest(
            test_date=test_date,
            operator=operator,
            measurement_1=measurement_1,
            overall_result=overall_result,
            notes=kwargs.get('notes', '')
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return test.id
    finally:
        db.close()
```

### 4. Créer les Endpoints API

Dans `backend/routers/weekly_tests.py` (ou daily/monthly), ajouter :

```python
@router.post("/my-new-test")
async def create_my_new_test(data: dict):
    """Endpoint pour créer un nouveau test"""
    try:
        test_id = database_helpers.save_my_new_test(
            test_date=parse_test_date(data.get('test_date')),
            operator=data['operator'],
            measurement_1=data['measurement_1'],
            overall_result=data['overall_result'],
            notes=data.get('notes', '')
        )
        return {"success": True, "test_id": test_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-new-test")
async def get_my_new_tests():
    """Endpoint pour récupérer tous les tests"""
    session = db.SessionLocal()
    try:
        tests = session.query(db.MyNewTest).order_by(
            db.MyNewTest.test_date.desc()
        ).all()
        return [{"id": t.id, "test_date": t.test_date.isoformat(), 
                 "operator": t.operator, "measurement_1": t.measurement_1,
                 "overall_result": t.overall_result} for t in tests]
    finally:
        session.close()
```

### 5. Redémarrer l'Application

```bash
cd backend
python -m uvicorn main:app --reload
```

La table sera créée automatiquement au démarrage.

## Conventions de Nommage

- **Nom de table** : `{frequency}_{test_name}` (ex: `weekly_my_new_test`)
- **Classe Python** : `{TestName}Test` (ex: `MyNewTest`)
- **Endpoints** : `/my-new-test` (kebab-case)

## Champs Standard Obligatoires

Tous les tests doivent avoir ces champs :
- `id` - Clé primaire auto-incrémentée
- `test_date` - Date du test (DateTime)
- `operator` - Nom de l'opérateur (String)
- `upload_date` - Date d'enregistrement (DateTime, auto)
- `overall_result` - Résultat global (String: "PASS"/"FAIL"/"WARNING")
- `notes` - Notes optionnelles (Text)

## Types de Colonnes

- `Float` - Mesures numériques
- `String` - Texte court, statuts
- `Text` - Texte long (notes)
- `DateTime` - Dates et heures
- `Integer` - Nombres entiers

## Exemple Complet

```python
# 1. Dans backend/database/weekly_tests.py
class GatingTest(Base):
    __tablename__ = "weekly_gating"
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    amplitude_mm = Column(Float, nullable=False)
    frequency_hz = Column(Float, nullable=False)

# 2. Dans backend/database_helpers.py
def save_gating_test(test_date, operator, amplitude_mm, frequency_hz, overall_result, **kwargs):
    db = SessionLocal()
    try:
        test = GatingTest(test_date=test_date, operator=operator, 
                         amplitude_mm=amplitude_mm, frequency_hz=frequency_hz,
                         overall_result=overall_result, notes=kwargs.get('notes', ''))
        db.add(test)
        db.commit()
        db.refresh(test)
        return test.id
    finally:
        db.close()

# 3. Dans backend/routers/weekly_tests.py
@router.post("/gating-test")
async def create_gating_test(data: dict):
    test_id = database_helpers.save_gating_test(
        test_date=parse_test_date(data.get('test_date')),
        operator=data['operator'],
        amplitude_mm=data['amplitude_mm'],
        frequency_hz=data['frequency_hz'],
        overall_result=data['overall_result']
    )
    return {"success": True, "test_id": test_id}
```

C'est tout ! La base de données est persistante et les nouvelles tables sont créées automatiquement.
