conda create --name lambda-deploy python=3.6
conda activate lambda-deploy
conda install -y xmltodict
conda install -y boto3

# site-packages
sitepackages=`python -c "import os, xmltodict; print(os.path.dirname(xmltodict.__file__))"`

pushd $sitepackages
zip -r9 /tmp/venv-arxiv.zip .
popd

zip -g /tmp/venv-arxiv.zip . DAWN.txt arxiv_query.py

conda env remove -n lambda-deploy
