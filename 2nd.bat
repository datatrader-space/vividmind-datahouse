REM **Always check for requirements.txt**
IF EXIST "requirements.txt" (
  ECHO Installing requirements from requirements.txt...
  pip install -r requirements.txt
  IF ERRORLEVEL 1 (
    ECHO Error: Failed to install requirements.
    EXIT /B 1
  )
  ECHO Installation successful.
) ELSE (
  ECHO Warning: requirements.txt not found. Skipping installation.
)

REM Start Django development server (replace 'yourproject' with your project name)
START "" python manage.py runserver 0.0.0.0:80 
START "" ngrok http 80
python main.py
PAUSE
