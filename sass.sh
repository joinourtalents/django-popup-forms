#!/bin/bash

pushd ../frontend
git pull
popd

cp ../frontend/css/sass/* static/project/css/sass/
sass --update static/project/css/sass:static/project/css
