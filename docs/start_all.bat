REM Avvia il container chiamato "zkp_project"
docker start mailhog
docker start zkp-mongo

timeout /t 5 >nul
REM Esegui il file Python
python ../start_all.py
