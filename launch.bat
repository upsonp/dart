@echo on
git pull origin master
if not exist "..\dart_env" python -m venv "..\dart_env"
call ..\dart_env\Scripts\activate.bat
dir/w
python -m pip install -r .\requirements.txt
python .\manage.py migrate
daphne dart.asgi:application