import subprocess, sys, os

scripts = [
    ('Task 2 — Data Engineering',         'task2_data_engineering.py'),
    ('Task 3 — EDA Visualizations',        'task3_eda_visualizations.py'),
    ('Task 4 — Advanced Visualizations',   'task4_advanced_visualizations.py'),
]

os.makedirs('outputs', exist_ok=True)
os.makedirs('data',    exist_ok=True)

for label, script in scripts:
    print(f'\n{"="*60}')
    print(f'Running: {label}')
    print('='*60)
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        print(f'\nERROR in {script} — stopping.')
        sys.exit(1)

print('\n' + '='*60)
print('All tasks complete. Output files in outputs/')
print('='*60)
print('\nTo launch the interactive dashboard:')
print('  streamlit run dashboard.py')
