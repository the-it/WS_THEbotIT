clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

pip3 :
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

cloc :
	echo "########## COUNT LOC ###########"
	cloc --exclude-dir=venv,__pycache__ --exclude-ext=xml,json .

pycodestyle :
	echo "########## PYCODESTYLE #########"
	pycodestyle --show-source --statistics --count

pylint :
	echo "############ PYLINT ############"
	pylint -j4 --rcfile .pylintrc scripts tools

bandit :
	echo "############ BANDIT ############"
	bandit -r scripts tools

gource :
	echo "############ GOURCE ############"
	gource -s 0.1 .

mypy :
	echo "############# MYPY #############"
	mypy scripts tools || true

safety :
	echo "############ SAFETY ############"
	safety check

flake8 :
	echo "############ FLAKE8 ############"
	flake8

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

code-climate-pre :
	echo "####### CODE CLIMATE PRE #######"
	curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter && \
	chmod +x ./cc-test-reporter && \
	./cc-test-reporter before-build

code-climate-post :
	echo "####### CODE CLIMATE POST ######"
	./cc-test-reporter format-coverage --output "coverage/codeclimate.${N}.json" && \
	./cc-test-reporter after-build --exit-code 0

clean-code-climate :
	echo "###### CLEAN CODE CLIMATE ######"
	rm -rf cc-test-reporter coverage || :

code-climate : clean-code-climate code-climate-pre coverage code-climate-post

codecov :
	echo "########### CODECOV ############"
	codecov

clean : clean-pyc clean-coverage clean-code-climate

pre-commit : pip3 quality integrationtest

quality : bandit flake8 pycodestyle pylint mypy

.PHONY : clean, code-climate, quality, pre-commit
