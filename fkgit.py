import os
import sys
import requests
import subprocess
import re

HOME_DIR = os.path.expanduser("~")
INSTALL_DIR = os.path.join(HOME_DIR, ".fkgit")
GITHUB_API_URL = "https://api.github.com/search/repositories"
DEPENDENCIES_INSTALLED = False

def ensure_install_dir():
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)

def detect_package_manager():
    if subprocess.run(["which", "apt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        return "apt"
    elif subprocess.run(["which", "pacman"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        return "pacman"
    elif subprocess.run(["which", "dnf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        return "dnf"
    elif subprocess.run(["which", "zypper"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        return "zypper"
    elif subprocess.run(["which", "emerge"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        return "emerge"
    else:
        return None

def is_base_devel_installed(package_manager):
    if package_manager == "apt":
        return subprocess.run(["dpkg", "-s", "build-essential"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    elif package_manager == "pacman":
        return subprocess.run(["pacman", "-Q", "base-devel"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    elif package_manager == "dnf":
        return subprocess.run(["rpm", "-q", "@development-tools"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    elif package_manager == "zypper":
        return subprocess.run(["rpm", "-q", "patterns-devel-base-devel_basis"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    elif package_manager == "emerge":
        return subprocess.run(["emerge", "--info", "@world"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    return False

def install_base_devel(package_manager):
    if is_base_devel_installed(package_manager):
        return
    if package_manager == "apt":
        subprocess.run(["sudo", "apt-get", "install", "-y", "build-essential"], check=True)
    elif package_manager == "pacman":
        subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "base-devel"], check=True)
    elif package_manager == "dnf":
        subprocess.run(["sudo", "dnf", "install", "-y", "@development-tools"], check=True)
    elif package_manager == "zypper":
        subprocess.run(["sudo", "zypper", "install", "-y", "patterns-devel-base-devel_basis"], check=True)
    elif package_manager == "emerge":
        subprocess.run(["sudo", "emerge", "--ask", "n", "@world"], check=True)
    else:
        print("Could not detect package manager.")
        sys.exit(1)

def parse_dependencies_from_readme(repo_path):
    readme_path = os.path.join(repo_path, "README.md")
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, "r") as f:
        content = f.read()
    dependencies_section = re.search(r"(Dependencies|Requirements):\s*(.*?)\n\n", content, re.IGNORECASE | re.DOTALL)
    if not dependencies_section:
        return []
    dependencies = re.findall(r"\b\w+\b", dependencies_section.group(2))
    return dependencies

def install_dependencies_from_readme(package_manager, repo_path):
    dependencies = parse_dependencies_from_readme(repo_path)
    if not dependencies:
        return
    for dep in dependencies:
        try:
            if package_manager == "apt":
                subprocess.run(["sudo", "apt-get", "install", "-y", dep], check=True)
            elif package_manager == "pacman":
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", dep], check=True)
            elif package_manager == "dnf":
                subprocess.run(["sudo", "dnf", "install", "-y", dep], check=True)
            elif package_manager == "zypper":
                subprocess.run(["sudo", "zypper", "install", "-y", dep], check=True)
            elif package_manager == "emerge":
                subprocess.run(["sudo", "emerge", "--ask", "n", dep], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to install dependency: {dep}")

def clone_repository(repo_url, repo_name):
    repo_path = os.path.join(INSTALL_DIR, repo_name)
    if os.path.exists(repo_path):
        return
    subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    return repo_path

def compile_package(repo_path):
    os.chdir(repo_path)
    if os.path.exists("Makefile"):
        subprocess.run(["sudo", "make"], check=True)
        subprocess.run(["sudo", "make", "install"], check=True)
    elif os.path.exists("CMakeLists.txt"):
        subprocess.run(["cmake", "."], check=True)
        subprocess.run(["sudo", "make"], check=True)
        subprocess.run(["sudo", "make", "install"], check=True)
    elif os.path.exists("package.json"):
        subprocess.run(["npm", "install"], check=True)
    elif os.path.exists("Cargo.toml"):
        subprocess.run(["cargo", "build", "--release"], check=True)
    else:
        print("Error: Could not detect build system.")
        sys.exit(1)

def install_package(repo_name, skip_confirmation=False, repo_number=None, auto_mode=False):
    if "/" in repo_name:
        repo_url = f"https://github.com/{repo_name}.git"
        repo_name = repo_name.split("/")[1]
        if not skip_confirmation and not auto_mode:
            confirm = input(f"Install repository {repo_name}? [Y/n]: ").strip().lower()
            if confirm == "n":
                return
        repo_path = clone_repository(repo_url, repo_name)
        if repo_path:
            package_manager = detect_package_manager()
            if package_manager:
                install_base_devel(package_manager)
                install_dependencies_from_readme(package_manager, repo_path)
            compile_package(repo_path)
        return

    repos = search_repositories(repo_name)
    if not repos:
        return

    print("Found repositories:")
    for i, repo in enumerate(repos):
        print(f"{i + 1}: {repo['full_name']} - {repo['description']}")

    if repo_number is not None:
        choice = repo_number - 1
    else:
        if auto_mode:
            choice = 0
        else:
            choice_input = input("Enter the number of the repository to install (or press Enter for the first one): ").strip()
            choice = int(choice_input) - 1 if choice_input else 0

    if choice < 0 or choice >= len(repos):
        return

    selected_repo = repos[choice]
    repo_url = selected_repo["clone_url"]
    repo_name = selected_repo["name"]

    if not skip_confirmation and not auto_mode:
        confirm = input(f"Install repository {repo_name}? [Y/n]: ").strip().lower()
        if confirm == "n":
            return

    repo_path = clone_repository(repo_url, repo_name)
    if repo_path:
        package_manager = detect_package_manager()
        if package_manager:
            install_base_devel(package_manager)
            install_dependencies_from_readme(package_manager, repo_path)
        compile_package(repo_path)

def search_repositories(query):
    response = requests.get(GITHUB_API_URL, params={"q": query})
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print("Error: Failed to search repositories.")
        sys.exit(1)

def search_packages(query):
    repos = search_repositories(query)
    if not repos:
        return
    print("Found repositories:")
    for i, repo in enumerate(repos):
        print(f"{i + 1}: {repo['full_name']} - {repo['description']}")

def update_and_rebuild_packages():
    for repo_name in os.listdir(INSTALL_DIR):
        repo_path = os.path.join(INSTALL_DIR, repo_name)
        if os.path.isdir(repo_path):
            os.chdir(repo_path)
            subprocess.run(["git", "pull"], check=True)
            compile_package(repo_path)

def remove_package(repo_name):
    repo_path = os.path.join(INSTALL_DIR, repo_name)
    if not os.path.exists(repo_path):
        return
    os.chdir(repo_path)
    try:
        subprocess.run(["sudo", "make", "uninstall"], check=True)
    except subprocess.CalledProcessError:
        try:
            subprocess.run(["sudo", "make", "remove"], check=True)
        except subprocess.CalledProcessError:
            pass
    os.chdir(HOME_DIR)
    subprocess.run(["sudo", "rm", "-rf", repo_path], check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  fkgit -S <repository>  - Install a package")
        print("  fkgit -S <user>/<repo> - Install a specific repository")
        print("  fkgit -S <repository> -n - Install without confirmation")
        print("  fkgit -S <repository> -l <number> - Install by number")
        print("  fkgit -S <repository> -c - Install in auto mode")
        print("  fkgit -Ss <query>      - Search for repositories")
        print("  fkgit -Suy            - Update and rebuild all packages")
        print("  fkgit -R <repository> - Remove a package")
        sys.exit(1)

    ensure_install_dir()
    package_manager = detect_package_manager()

    if sys.argv[1] == "-S":
        if len(sys.argv) < 3:
            print("Usage: fkgit -S <repository>")
            sys.exit(1)
        repo_name = sys.argv[2]
        skip_confirmation = "-n" in sys.argv
        repo_number = None
        auto_mode = "-c" in sys.argv
        if "-l" in sys.argv:
            try:
                repo_number = int(sys.argv[sys.argv.index("-l") + 1])
            except (ValueError, IndexError):
                print("Invalid number for -l flag.")
                sys.exit(1)
        if package_manager:
            install_base_devel(package_manager)
        install_package(repo_name, skip_confirmation, repo_number, auto_mode)
    elif sys.argv[1] == "-Ss":
        if len(sys.argv) != 3:
            print("Usage: fkgit -Ss <query>")
            sys.exit(1)
        query = sys.argv[2]
        search_packages(query)
    elif sys.argv[1] == "-Suy":
        if package_manager:
            install_base_devel(package_manager)
        update_and_rebuild_packages()
    elif sys.argv[1] == "-R":
        if len(sys.argv) != 3:
            print("Usage: fkgit -R <repository>")
            sys.exit(1)
        repo_name = sys.argv[2]
        remove_package(repo_name)
    else:
        print("Unknown command.")
        sys.exit(1)

if __name__ == "__main__":
    main()
