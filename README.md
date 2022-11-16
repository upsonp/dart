# Requirements
* Python 3.10+
* Git

# Recommendation
Download (Pycharm)[https://www.jetbrains.com/pycharm/] and use the terminal to clone and work with the application. Pycharm comes with the basic tools required to get started. If Git and python are installed on the local machine this process can be completed from a command line without the Pycharm IDE.

# Pycharm Setup

`git clone https://github.com/upsonp/dart.git`  
`python -m pip install -r requirements.txt`  
`python manage.py migrate`  
`daphne dart.asgi:application`  
  
open web browser, navigate to `localhost:8000`

to stop the server press `ctrl+c`

# Command Line Setup

Open commandline, navigate to parent directory where applciation will be deployed.
`git clone https://github.com/upsonp/dart.git`  
`cd dart`  
`python -m venv dart_env`  
`.\dart_env\Scripts\activate`  
`python -m pip install -r requirements.txt`  
`python manage.py migrate`  
`daphne dart.asgi:application`
