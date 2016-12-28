# create virtualenv
vex --python python3.3 -m pythondir
# Install dependencies
vex --python python3.3 pythondir pip install -r requirements.txt
# run server
vex pythondir python server.py

