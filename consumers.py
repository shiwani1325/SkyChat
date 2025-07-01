import os
import glob

apps = ['custom', 'employee', 'org', 'superadmin', 'chat']

for app in apps:
    path = os.path.join(app, 'migrations')
    files = glob.glob(os.path.join(path, '*.py'))
    for file in files:
        if not file.endswith('__init__.py'):
            os.remove(file)
    # Also remove .pyc files
    pyc_files = glob.glob(os.path.join(path, '__pycache__', '*.pyc'))
    for pyc_file in pyc_files:
        os.remove(pyc_file)
