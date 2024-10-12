import venv
import subprocess
import sys

def create_venv():
    venv.create('venv', with_pip=True)

def install_requirements():
    pip = 'venv\\Scripts\\pip.exe' if sys.platform == 'win32' else 'venv/bin/pip'
    subprocess.check_call([pip, 'install', '-r', 'requirements.txt'])

if __name__ == '__main__':
    create_venv()
    install_requirements()
    print("Environment setup complete. Activate it with:")
    if sys.platform == 'win32':
        print("venv\\Scripts\\activate")
    else:
        print("source venv/bin/activate")