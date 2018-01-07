#!/usr/bin/env sh

export CC_TEST_REPORTER_ID=f3b7cf9220d85b6dde901a10d6f18747720138f87ed4f648bb7364d52f5310bb
coverage run test/all_test.py
coverage xml
./cc-test-reporter format-coverage --output "coverage/codeclimate.$N.json"
echo $TRAVIS_TEST_RESULT
./cc-test-reporter after-build --exit-code $TRAVIS_TEST_RESULT