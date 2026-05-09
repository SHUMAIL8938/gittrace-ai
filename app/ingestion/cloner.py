import os
import tempfile
import shutil
import git  


IGNORE_DIRS = {
    ".git",".github", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "target", "vendor",
    ".idea", ".vscode", "eggs", ".eggs",".docs","site","venv","test","tests"
}
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rs", ".cpp", ".c", ".h", ".cs", ".rb", ".php",
    ".swift", ".kt", ".scala", ".r", ".sh", ".yaml",
    ".yml", ".toml", ".json", ".md", ".sql", ".html", ".css"
}
def clone_repo(github_url:str)-> tuple[str,list[str]]:
    repo_dir=tempfile.mkdtemp()
    git.Repo.clone_from(github_url,repo_dir,depth=1)
    file_paths=[]
    for root,dirnames,filenames in os.walk(repo_dir):
        dirnames[:]=[d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            _,ext=os.path.splitext(filename)
            if ext.lower()not in ALLOWED_EXTENSIONS:
                continue
            full_path=os.path.join(root,filename)
            file_paths.append(full_path)
    return repo_dir,file_paths
def cleanup_repo(repo_dir:str):
    shutil.rmtree(repo_dir,ignore_errors=True)