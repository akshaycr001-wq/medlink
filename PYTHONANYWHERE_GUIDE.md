# PythonAnywhere Deployment Guide for MedLink

To host your project on PythonAnywhere, follow these steps:

### 1. Create an Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com/) and create a free account.

### 2. Upload Your Code
The easiest way is to use Git. Open the **Bash Console** in PythonAnywhere and run:
```bash
git clone https://github.com/yourusername/your-repo-name.git
```

### 3. Create a Virtual Environment
In the PythonAnywhere Bash console:
```bash
mkvirtualenv --python=/usr/bin/python3.10 medlink-venv
pip install -r requirements.txt
```

### 4. Configure the Web Tab
1. Go to the **Web** tab in PythonAnywhere.
2. Click **Add a new web app**.
3. Select **Manual Configuration** -> **Python 3.10**.
4. Set the **Virtualenv** path to: `/home/yourusername/.virtualenvs/medlink-venv`
5. Click the **WSGI configuration file** link.

### 5. Update the WSGI Configuration
Replace the content of the WSGI file with the following:

```python
import sys
import os

# Path to your project
path = '/home/yourusername/your-repo-name'
if path not in sys.path:
    sys.path.append(path)

os.environ['FLASK_ENV'] = 'production'

from app import app as application
```

### 6. Final Steps
1. Go back to the **Web** tab and click **Reload**.
2. Your site will be live at `yourusername.pythonanywhere.com`.

---
**Note**: Since you are using SQLite, your database will be saved in the `instance/` folder on PythonAnywhere and will be persistent!
