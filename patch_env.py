with open('api.py', 'r') as f:
    text = f.read()

import_env = """import os
import json
import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
"""
text = text.replace("import os\nimport json\nimport datetime\nfrom typing import List, Dict, Any, Optional\nfrom pydantic import BaseModel", import_env)

with open('api.py', 'w') as f:
    f.write(text)

with open('utils.py', 'r') as f:
    text = f.read()

text = text.replace("import os\nimport json\nimport re\nimport sqlite3\nfrom datetime import datetime", "import os\nimport json\nimport re\nimport sqlite3\nfrom datetime import datetime\nfrom dotenv import load_dotenv\n\nload_dotenv()")

with open('utils.py', 'w') as f:
    f.write(text)

with open('app.py', 'r') as f:
    text = f.read()
    
text = text.replace("import streamlit as st\nimport pandas as pd\nimport requests\nfrom datetime import datetime\nimport base64", "import streamlit as st\nimport pandas as pd\nimport requests\nfrom datetime import datetime\nimport base64\nfrom dotenv import load_dotenv\nload_dotenv()")
with open('app.py', 'w') as f:
    f.write(text)
