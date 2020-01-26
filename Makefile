# tools

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
	rm requirements.txt requirements-dev.txt
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in
	pip-sync requirements.txt requirements-dev.txt

# quality

pycodestyle :
	echo "########## PYCODESTYLE #########"
	pycodestyle --show-source --statistics --count

pylint :
	echo "############ PYLINT ############"
	pylint -j4 --rcfile .pylintrc scripts tools infrastructure

bandit :
	echo "############ BANDIT ############"
	bandit -r scripts tools infrastructure

mypy :
	echo "############# MYPY #############"
	mypy scripts tools

safety :
	echo "############ SAFETY ############"
	safety check

flake8 :
	echo "############ FLAKE8 ############"
	flake8

# testing and coverage

unittest :
	echo "########### UNITTEST ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	nosetests

integrationtest :
	echo "######## INTEGRATIONTEST #######"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	export INTEGRATION=1 && \
	coverage run tst_runner.py && \
	coverage xml

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	export INTEGRATION=1 && \
	coverage run tst_runner.py && \
	coverage xml

coverage-html : coverage
	echo "######### COVERAGE HTML ########"
	coverage html -d .coverage_html
	python -c "import webbrowser, os; webbrowser.open('file://' + os.path.realpath('.coverage_html/index.html'))"

clean-coverage :
	echo "######## CLEAN COVERAGE ########"
	rm -rf .coverage coverage.xml .coverage_html || :

codecov :
	echo "########### CODECOV ############"
	codecov

# infrastructure

aws_deploy :
	echo "######## AWS DEPLOY #########"
	cdk bootstrap
	cdk deploy

aws_diff :
	echo "######### AWS DIFF ##########"
	cdk bootstrap
	cdk diff

# phony targets

clean : clean-pyc clean-coverage

pre-commit : update_pip3 quality integrationtest

quality : bandit flake8 pycodestyle pylint mypy

.PHONY : clean, quality, pre-commit
