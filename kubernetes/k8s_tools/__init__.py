# k8s_tools/__init__.py


# Remove all content from the /tmp folder
import os
os.system("rm -rf /tmp/*")
if "PYTHONPATH" in os.environ:
    del os.environ["PYTHONPATH"]

def get_dir_tree(start_path, indent=0):
    """Recursively generates a directory tree as a string."""
    tree = ""
    items = os.listdir(start_path)
    for item in items:
        item_path = os.path.join(start_path, item)
        if os.path.isdir(item_path):
            tree += "    " * indent + f"📁 {item}\n"
            # tree += get_dir_tree(item_path, indent + 1)
        else:
            tree += "    " * indent + f"📄 {item}\n"
    return tree

# Specify the directory you want to start with
start_directory = "/tmp/kubiya_shared_tools"
dir_tree = get_dir_tree(start_directory)

raise Exception(f"{dir_tree}")
raise Exception(f"environ: {os.environ}")

from .tools import *
