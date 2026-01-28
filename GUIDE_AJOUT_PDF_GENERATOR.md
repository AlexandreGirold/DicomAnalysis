# Guide : Ajouter un Generateur PDF

## 1. Creer le Generateur

Fichier : `backend/services/pdf_generators/mon_test_generator.py`

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

def generate_mon_test_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    elements.append(Paragraph("Rapport MonTest"))
    
    info = [
        ["Date:", data.get("test_date", "N/A")],
        ["Operateur:", data.get("operator", "N/A")],
        ["Resultat:", data.get("overall_result", "N/A")]
    ]
    t = Table(info)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

def generate_mon_test_trend_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    elements.append(Paragraph("Tendances MonTest"))
    
    table_data = [["Date", "Operateur", "Resultat"]]
    for test in data.get('tests', []):
        table_data.append([
            test.get("test_date", "N/A"),
            test.get("operator", "N/A"),
            test.get("overall_result", "N/A")
        ])
    
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
```

## 2. Ajouter les Routes

Fichier : `backend/routers/reports.py`

```python
from services.pdf_generators.mon_test_generator import generate_mon_test_pdf, generate_mon_test_trend_pdf

@router.get("/mon-test/{test_id}/pdf")
async def get_mon_test_pdf(test_id: int):
    db = SessionLocal()
    try:
        test = db.query(MonTestTable).filter(MonTestTable.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404)
        
        data = {
            "test_date": str(test.test_date),
            "operator": test.operator,
            "overall_result": test.overall_result
        }
        
        pdf_bytes = generate_mon_test_pdf(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=mon_test_{test_id}.pdf"}
        )
    finally:
        db.close()

@router.get("/mon-test-trend")
async def get_mon_test_trend(start_date: str, end_date: str, format: str = "json"):
    db = SessionLocal()
    try:
        tests = db.query(MonTestTable).filter(
            MonTestTable.test_date >= start_date,
            MonTestTable.test_date <= end_date
        ).all()
        
        data = {
            "tests": [{"test_date": str(t.test_date), "operator": t.operator, 
                      "overall_result": t.overall_result} for t in tests],
            "date_range": {"start": start_date, "end": end_date}
        }
        
        if format == "pdf":
            pdf_bytes = generate_mon_test_trend_pdf(data)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=mon_test_tendances.pdf"}
            )
        
        return data
    finally:
        db.close()
```

## 3. Debloquer Frontend

### trends.html
Retirer `disabled` :
```html
<option value="mon_test">Mon Test</option>
```

### trends.js
Ajouter endpoint :
```javascript
function getEndpointForTestType(testType) {
    const endpoints = {
        'piqt': '/reports/piqt-trend',
        'mon_test': '/reports/mon-test-trend'
    };
    return endpoints[testType];
}
```

Ajouter dans generatePDF() :
```javascript
else if (testType === 'mon_test') {
    url = `${API_BASE_URL}/reports/mon-test-trend?start_date=${startDate}&end_date=${endDate}&format=pdf`;
    const response = await fetch(url);
    const blob = await response.blob();
    const a = document.createElement('a');
    a.href = window.URL.createObjectURL(blob);
    a.download = `mon_test_${startDate}_${endDate}.pdf`;
    a.click();
}
```

