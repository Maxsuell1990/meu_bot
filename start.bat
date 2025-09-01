@echo off
echo Iniciando o bot...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
