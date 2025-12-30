from database import SessionLocal, LeafPositionTest, LeafPositionResult

session = SessionLocal()

tests = session.query(LeafPositionTest).all()
print(f'Total tests: {len(tests)}')

for t in tests:
    blade_count = session.query(LeafPositionResult).filter(
        LeafPositionResult.test_id == t.id
    ).count()
    print(f'Test {t.id}: operator={t.operator}, date={t.test_date.strftime("%Y-%m-%d")}, blades={blade_count}')

session.close()
