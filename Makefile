#####################
### PACKAGE STUFF ###
#####################
clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

cloc :
	echo "########## COUNT LOC ###########"
	cloc --exclude-dir=venv,__pycache__ --exclude-ext=xml,json .

gource :
	echo "############ GOURCE ############"
	gource -s 0.1 .

# dependency management

install_pip :
	echo "########## UPDATE PIP ##########"
	pip install --upgrade pip

pip3 : install_pip
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

pip3-dev : install_pip
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt -r requirements-dev.txt

update_pip3 : install_pip
	echo "##### UPDATE REQUIREMENTS ######"
	pip install pip-tools -U
	pip install wheel -U
	rm requirements.txt requirements-dev.txt || true
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in
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
	mypy service tools

safety :
	echo "############ SAFETY ############"
	safety check

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
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	python tst_runner.py

integrationtest : clean-coverage
	echo "######## INTEGRATIONTEST #######"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	export WS_REAL_DATA=1 && \
	unset WS_REAL_WIKI && \
	coverage run tst_runner.py && \
	coverage xml

wikitest : clean-coverage
	echo "########### WIKITEST ###########"
	export WS_REAL_WIKI=1 && \
	unset WS_REAL_DATA && \
	coverage run tst_runner.py && \
	coverage xml

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	unset WS_REAL_WIKI && \
	unset WS_REAL_DATA && \
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	coverage run tst_runner.py && \
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

#############
### PHONY ###
#############
clean : clean-pyc clean-coverage

pre-commit : update_pip3 quality unittest

quality : bandit flake8 pycodestyle pylint mypy

.PHONY : clean, quality, pre-commit
