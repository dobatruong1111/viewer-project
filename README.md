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
Development
-----------
For browsing code in IDE (i.e Visual Code Studio) run below commands then open the project in your IDE
```shell
poetry shell
```
