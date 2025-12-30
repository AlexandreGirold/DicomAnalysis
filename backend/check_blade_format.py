from database.queries import get_leaf_position_test_by_id

test = get_leaf_position_test_by_id(5)
blades = test['blade_results'] if test else []

print('Number of blades:', len(blades))
print('\nFirst 5 blade_pairs:')
for i, b in enumerate(blades[:5]):
    print(f'  {i+1}. {b["blade_pair"]} - size: {b["field_size_mm"]}mm')
