#####################
### PACKAGE STUFF ###
#####################
clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

# dependency management

install :
	echo "##### INSTALL REQUIREMENTS #####"
	uv sync

install-dev :
	echo "##### INSTALL DEV REQUIREMENTS #####"
	uv sync --all-extras

update :
	echo "##### UPDATE REQUIREMENTS ######"
	uv lock --upgrade

###############
### QUALITY ###
###############
pycodestyle :
	echo "########## PYCODESTYLE #########"
	uv run pycodestyle --show-source --statistics --count

pylint :
	echo "############ PYLINT ############"
	uv run pylint -j4 --rcfile .pylintrc service tools

bandit :
	echo "############ BANDIT ############"
	uv run bandit -r service tools

mypy :
	echo "############# MYPY #############"
	uv run mypy --check-untyped-defs  service tools

flake8 :
	echo "############ FLAKE8 ############"
	uv run flake8

############################
### TESTING AND COVERAGE ###
############################
unittest :
	echo "########### UNITTEST ###########"
	unset WS_REAL_WIKI && \
	unset WS_REAL_DATA && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	export PYTHONUNBUFFERED=1 && \
	.venv/bin/nose2 -v service tools

integrationtest : clean-coverage
	echo "######## INTEGRATIONTEST #######"
	export WS_REAL_DATA=1 && \
	unset WS_REAL_WIKI && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	export PYTHONUNBUFFERED=1 && \
	.venv/bin/nose2 -v --with-coverage service tools && \
	uv run coverage xml

wikitest : clean-coverage
	echo "########### WIKITEST ###########"
	export WS_REAL_WIKI=1 && \
	unset WS_REAL_DATA && \
	export PYTHONUNBUFFERED=1 && \
	.venv/bin/nose2 -v --with-coverage service tools && \
	uv run coverage xml

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	unset WS_REAL_WIKI && \
	unset WS_REAL_DATA && \
	export PYWIKIBOT_NO_USER_CONFIG=1 && \
	.venv/bin/nose2 -v --with-coverage && \
	uv run coverage xml

coverage-html : wikitest
	echo "######### COVERAGE HTML ########"
	uv run coverage html -d .coverage_html
	uv run python -c "import webbrowser, os; webbrowser.open('file://' + os.path.realpath('.coverage_html/index.html'))"

clean-coverage :
	echo "######## CLEAN COVERAGE ########"
	rm -rf .coverage coverage.xml .coverage_html || :

codecov :
	echo "########### CODECOV ############"
	uv run codecov

#############
### TOOLS ###
#############
gource :
	echo "############ GOURCE ############"
	gource -s 0.1 .

cloc :
	echo "########## COUNT LOC ###########"
	cloc --exclude-dir=venv,__pycache__ --exclude-ext=xml,json,html,txt,png .

clean_data :
	echo "########## CLEAN DATA ###########"
	rm -rf service/ws_re/register/data

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

pre-commit : update quality unittest

quality : flake8 pycodestyle pylint mypy unittest

.PHONY : clean, quality, pre-commit
