Viewer-Server
=============
A viewer server is a radiological viewer developed for clinical professionals.

Run
-----------
Clone the project and run with command
```shell
poetry install
```
Find the location in which python packages are being install, i.e,  ~/.cache/pypoetry/virtualenvs/fastapi-viewer-CygDWbJp-py3.10

Source environment
```shell
source ~/.cache/pypoetry/virtualenvs/fastapi-viewer-CygDWbJp-py3.10/bin/activate
```
Run app
```shell
cd ./src && uvicorn main:app --workers 4 
```
Viewer URL
```shell
http://localhost:8000/viewer/index.html?session=3a4db36d-b5f9-4059-b3e9-1761c15cab5d&studies=1.2.410.200024.1.1.0.20220531.143936.1&userID=1234 
```

Development
-----------
For browsing code in IDE (i.e Visual Code Studio) run below commands then open the project in your IDE
```shell
poetry shell
```
