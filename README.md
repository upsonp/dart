# Requirements
* Python 3.10+
* Git

# Recommendation
My recommendation is to download (Pycharm)[https://www.jetbrains.com/pycharm/] and use the terminal to clone and work with the application. Pycharm comes with the basic tools required to get started.

# Setup

`git clone https://github.com/upsonp/dart.git`  
`python -m pip install -r requirements.txt`  
`python manage.py migrate`  
`daphne dart.asgi:application`  
  
open web browser, navigate to `localhost:8000`

to stop the server press `ctrl+c`
