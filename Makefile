clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

pip3 :
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

pip3-all : pip3
	echo "### INSTALL ALL REQUIREMENTS ###"
	pip3 install -r requirements_dev.txt

pycodestyle :
	echo "########## PYCODESTYLE #########"
	pycodestyle --show-source --statistics --count

pylint : 
	echo "############ PYLINT ############"
	pylint -j2 --rcfile .pylintrc scripts tools

bandit :
	echo "############ BANDIT ############"
	bandit -r .

mypy :
	echo "############# MYPY #############"
	mypy .

safety :
	echo "############ SAFETY ############"
	safety check

flake8 :
	echo "############ FLAKE8 ############"
	flake8

unittest :
	echo "########### UNITTEST ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	python -m unittest test/all_tests.py

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	coverage run test/all_tests.py && \
	coverage xml

coverage_html : coverage
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

codacy :
	echo "############ CODACY ############"
	python-codacy-coverage -r coverage.xml

clean : clean-pyc clean-coverage clean-code-climate

quality : bandit coverage flake8 pycodestyle pylint

.PHONY : clean, code-climate, quality
