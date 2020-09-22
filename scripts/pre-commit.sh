#! /bin/sh

banner_first=1
function banner () {
  if [ $banner_first -gt 0 ];
  then
    banner_first=0
  else
    echo
    echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  fi
  echo
  echo "* $1"
  echo "  $2"
  echo
}

set -e

# echo
# echo "Run test"
# echo
# bash scripts/run_tests.sh

banner "Run isort" "docker-compose exec django isort . --check --diff"
docker-compose exec django isort . --check --diff

banner "Run autopep8" "docker-compose exec django autopep8 --exit-code --diff -r ."
docker-compose exec django autopep8 --exit-code --diff -r .

banner "Run flake8" "docker-compose exec django flake8"
docker-compose exec django flake8

banner "Run flake8" "docker-compose exec django pylama"
docker-compose exec django pylama

set +e

banner "Run pip list --outdated" "docker-compose exec django pip3 list --outdated"
docker-compose exec django pip3 list --outdated
