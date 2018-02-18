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
	pycodestyle --show-source --statistics --count  || :

pylint : 
	echo "############ PYLINT ############"
	pylint scripts tools  || :

flake8 :
	echo "############ FLAKE8 ############"
	flake8 --exit-zero --benchmark  || :

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
	coverage run test/all_test.py && \
	coverage xml

clean-coverage :
	echo "######## CLEAN COVERAGE ########"
	rm .coverage coverage.xml || :

code-climate-pre :
	echo "####### CODE CLIMATE PRE #######"
	curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
	chmod +x ./cc-test-reporter
	./cc-test-reporter before-build

code-climate-post :
	echo "####### CODE CLIMATE POST ######"
	export CC_TEST_REPORTER_ID=f3b7cf9220d85b6dde901a10d6f18747720138f87ed4f648bb7364d52f5310bb
	./cc-test-reporter format-coverage --output "coverage/codeclimate.$N.json"
	./cc-test-reporter after-build --exit-code $TRAVIS_TEST_RESULT

clean-code-climate : 
	rm -rf cc-test-reporter coverage || :

code-climate : clean-code-climate code-climate-pre coverage code-climate-post

codecov : coverage
	codecov --token=bb224da4-b91a-4080-b106-cb7bb5d84595

clean : clean-pyc clean-coverage clean-code-climate

quality : pycodestyle flake8 pylint coverage

.PHONY : clean, code-climate, quality
