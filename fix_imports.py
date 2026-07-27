import os
import re

cove_dir = "/home/lokesh-yadav/Desktop/projects/Major-Project/cove"

module_to_package = {
    "vision_config": "config",
    "ai_engine": "engines",
    "cluster_engine": "engines",
    "person_manager": "engines",
    "search_engine": "engines",
    "vector_storage": "engines",
    "prepare_lfw": "pipeline",
    "download_models": "pipeline",
}

def fix_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    for mod, pkg in module_to_package.items():
        pattern = r'^(from\s+)' + re.escape(mod) + r'(\s+import)'
        content = re.sub(pattern, r'\1' + pkg + '.' + mod + r'\2', content, flags=re.MULTILINE)
        
        pattern2 = r'^(import\s+)' + re.escape(mod) + r'(\s*(?:$|\n|#))'
        content = re.sub(pattern2, 'from ' + pkg + r' import ' + mod + r'\2', content, flags=re.MULTILINE)

    if content != original_content:
        if "/pipeline/" in filepath or "/ui/" in filepath or "/api/" in filepath:
            if "sys.path.append" not in content and "sys.path.insert" not in content and "import sys" not in content:
                sys_path_hack = "import sys\nimport os\n_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nif _project_root not in sys.path:\n    sys.path.insert(0, _project_root)\n\n"
                
                # Insert at the top of the file, after any docstrings
                # Simplification: just prepend
                content = sys_path_hack + content

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, _, files in os.walk(cove_dir):
    for f in files:
        if f.endswith('.py'):
            fix_imports(os.path.join(root, f))
