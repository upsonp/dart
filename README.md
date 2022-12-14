# Requirements
* Python 3.10+
* Git

# Recommendation
Download (Pycharm)[https://www.jetbrains.com/pycharm/] and use the terminal to clone and work with the application. Pycharm comes with the basic tools required to get started. If Git and python are installed on the local machine this process can be completed from a command line without the Pycharm IDE.

# Pycharm Setup

* Open a terminal view  
* Navigate to parent directory where applciation will be deployed 
* `git clone https://github.com/upsonp/dart.git`  
* Open the dart directroy as a new project
* `python -m pip install -r requirements.txt`  
* `python manage.py migrate`  
  
# Command Line Setup

* Open commandline  
* Navigate to parent directory where applciation will be deployed  
* `git clone https://github.com/upsonp/dart.git`  
* `cd dart`  
* `python -m venv dart_env`  
* `.\dart_env\Scripts\activate`  
* `python -m pip install -r requirements.txt`  
* `python manage.py migrate`

# Settings
Django uses a secret key to keep track of communication encryption, when in production this key should be private. As such, DART has a file called the `settings_local_default.py` file in the `dart/dart/` directory. The file needs to be copyed and renamed `settings_local.py` and the secret key set.


# Start the server
* `daphne dart.asgi:application`

# Accessing DART
open web browser, navigate to `localhost:8000`

to stop the server press `ctrl+c` with the terminal window selected
