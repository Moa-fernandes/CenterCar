# conftest.py

import os
import sys

# adiciona a raiz do projeto ao path de importação
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
