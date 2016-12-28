# create virtualenv
vex --python python3.3 -m pythondir
# Install dependencies
vex --python python3.3 pythondir pip install -r requirements.txt
# install different version of gmplot with infowindow
git clone git@github.com:sgonzaloc/gmplot.git
cd gmplot
vex --python python3.3 pythondir pip install -e .
# run script
vex --python python3.3 pythondir python run.py --latitude 1 --longitude 2 --radius 1

