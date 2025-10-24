#####################
### PACKAGE STUFF ###
#####################
clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

# dependency management

install_pip_tools :
	echo "########## UPDATE PIP ##########"
	pip install --upgrade pip pip-tools setuptools wheel

pip3 : install_pip_tools
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

pip3-dev : install_pip_tools
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt -r requirements-dev.txt

update_pip3 : install_pip_tools
	echo "##### UPDATE REQUIREMENTS ######"
	rm requirements.txt requirements-dev.txt || true
	pip-compile --resolver=backtracking --output-file requirements.txt requirements.in
	pip-compile --resolver=backtracking --output-file requirements-dev.txt requirements-dev.in
	pip-sync requirements.txt requirements-dev.txt

###############
### QUALITY ###
###############
pycodestyle :
	echo "########## PYCODESTYLE #########"
	pycodestyle --show-source --statistics --count

pylint :
	echo "############ PYLINT ############"
	pylint -j4 --rcfile .pylintrc service tools

bandit :
	echo "############ BANDIT ############"
	bandit -r service tools

mypy :
	echo "############# MYPY #############"
	mypy --check-untyped-defs  service tools

flake8 :
	echo "############ FLAKE8 ############"
	flake8

############################
### TESTING AND COVERAGE ###
############################
unittest :
	echo "########### UNITTEST ###########"
	unset WS_REAL_WIKI && \
	unset WS_REAL_DATA && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	export PYTHONUNBUFFERED=1 && \
	venv/bin/nose2 -v service tools

integrationtest : clean-coverage
	echo "######## INTEGRATIONTEST #######"
	export WS_REAL_DATA=1 && \
	unset WS_REAL_WIKI && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	export PYTHONUNBUFFERED=1 && \
	venv/bin/nose2 -v --with-coverage service tools && \
	coverage xml

wikitest : clean-coverage
	echo "########### WIKITEST ###########"
	export WS_REAL_WIKI=1 && \
	unset WS_REAL_DATA && \
	export PYTHONUNBUFFERED=1 && \
	venv/bin/nose2 -v --with-coverage service tools && \
	coverage xml

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	unset WS_REAL_WIKI && \
	unset WS_REAL_DATA && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	venv/bin/nose2 -v --with-coverage && \
	coverage xml



coverage-html : wikitest
	echo "######### COVERAGE HTML ########"
	coverage html -d .coverage_html
	python -c "import webbrowser, os; webbrowser.open('file://' + os.path.realpath('.coverage_html/index.html'))"

clean-coverage :
	echo "######## CLEAN COVERAGE ########"
	rm -rf .coverage coverage.xml .coverage_html || :

codecov :
	echo "########### CODECOV ############"
	codecov

#############
### STUFF ###
#############
gource :
	echo "############ GOURCE ############"
	gource -s 0.1 .

cloc :
	echo "########## COUNT LOC ###########"
	cloc --exclude-dir=venv,__pycache__ --exclude-ext=xml,json .

############
### OCRS ###
############

upload_ocrs_prd :
	echo "####### UPLOAD OCRS PRD ########"
	aws s3 sync service/ws_re/download_upload/ocrs/txt s3://wiki-bots-re-ocr-prd --profile ersotech_prd

upload_ocrs_tst :
	echo "####### UPLOAD OCRS TST ########"
	aws s3 sync service/ws_re/download_upload/ocrs/txt s3://wiki-bots-re-ocr-tst --profile ersotech_tst

#############
### PHONY ###
#############
clean : clean-pyc clean-coverage

pre-commit : update_pip3 quality unittest

quality : flake8 pycodestyle pylint mypy unittest

.PHONY : clean, quality, pre-commit
