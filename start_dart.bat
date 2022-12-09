@echo on
git pull origin master > log.txt
if not exist "..\dart_env" python -m venv "..\dart_env" >> log.txt
call ..\dart_env\Scripts\activate.bat >> log.txt
python -m pip install -r .\requirements.txt >> log.txt
python .\manage.py migrate >> log.txt
daphne dart.asgi:application >> log.txt