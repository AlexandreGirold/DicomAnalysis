from database.config import SessionLocal
from database.weekly_tests import PIQTTest

db = SessionLocal()
tests = db.query(PIQTTest).all()
print(f'Total PIQT tests: {len(tests)}')
for t in tests:
    rj_len = len(t.results_json) if t.results_json else 0
    print(f'ID {t.id}: results_json={rj_len} chars, snr={t.snr_value}, unif={t.uniformity_value}, ghost={t.ghosting_value}')
db.close()
