# README FOR DEVELOPERS AND DEPLOYMENT

Warehouse Management System ....

## Prerequirities
You should install all of these prerequirites to make the application running smoothly

Open *command-prompt* for Windows

Open *terminal* for Linux

Open *Homebrew* for Mac

### Docker Latest Version
#### For Windows
Installation using Winget (Windows 10/11)
```
winget install --id Docker.DockerDesktop --source winget
```

#### For Linux Debian 
```
sudo apt-get install ./docker-desktop-amd64.deb
```
#### For Linux Fedora
```
sudo dnf install ./docker-desktop-x86_64.rpm
```
#### For MacOS 
Install Homebrew First:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Then
```
brew update
brew install --cask docker
```

### Python 3.10 or Later
#### For Windows
Installation using Winget (Windows 10/11)
```
winget install --id Python.Python.3 --source winget
```
or
```
curl -Lo python-installer.exe https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe
```
```
python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
del python-installer.exe
```
#### For Linux Debian
```
sudo apt install -y python3 python3-venv python3-pip
```
#### For Linux Fedora
```
sudo dnf install -y python3 python3-virtualenv python3-pip
```
#### For MacOS
Install Homebrew First:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Then
```
brew update
brew install python
```
#### To verify python installation
```
python --version
pip --version
```

### Installing Git
For convenient, perhaps you need to instal Git on your machine.

#### For Windows
```
winget install --id Git.Git -e --source winget
```

#### For Linux Debian
```
apt-get install git
```

#### For Linux Fedora
```
dnf install git
```

#### For MacOS
```
brew install git-gui
```

## Adding this repository into your PC
Open your CMD on Windows, or Terminal on Linux, or Homebrew for MacOS

Copy paste and run this command
```
git clone https://github.com/ghanrabban/Warehouse-Management-System.git
```

After you dwonload the repo, you can find it manually on the default location (Usually for Windows at C:\Users\[Name])
#### Windows
```
cd C:\(GitHub Repo Location)
```

#### Linux and MacOS
```
cd /home/(GitHub Repo Location)
```

## Development Stage
For simplicity, you can copy paste and run this command
```
pip install -r requirements.txt
```

#### Python Serial
```
pip install pyserial
```

#### Python Barcode Scanner
```
pip install python‑barcode
```

#### Python MySQL
```
pip install mysql-connector-python
```

#### Web Develepmont Framework: Django 4.2
```
python -m pip install Django==5.2.4
```

#### Django CurrentUser
```
pip install django-currentuser
```

## How to Compose and Containerizing MySQL into Docker

```
docker compose down
docker compose up -d
```

After that, you need to build a conternizer Docker Container
```
docker compose up --build
```

## How to Run a Debug Server
Open the specific directory
```
cd GitHub/warehouse-management-system/database
```
Run this command
```
python manage.py runserver 127.0.0.1:8001
```
Then open this link on the browser
```
http://127.0.0.1:8001/
```

#### MySQL Django debug command
```
mysql -h 127.0.0.1 -P 3306 -u wms_user -pwms_pass wms_demo
```
```
SELECT * FROM scanned_barcodes;
```
#### IMPORTANT FOR ADMIN LOGIN

Username: 
```
GEF_T3
```

Email: (leave it blank)

Password: 
```
admin_elektronika_t3
```

## NOTES FOR DEVELOPMENT
Create an import/export PDF report mechanism inside "History" tab or "Events" tab

Create the availabe stock indicator (red, yellow, green)
