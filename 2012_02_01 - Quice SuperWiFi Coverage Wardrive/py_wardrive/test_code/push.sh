#!/bin/bash

TARGETS="warbox9"

for TARG in $TARGETS
do	
	echo "--> Pushing code to $TARG ..."
	echo "scp ~/mycode/py_wardrive/*.py root@$TARG:~/py_wardrive/"
	scp ~/mycode/py_wardrive/*.py root@$TARG:~/py_wardrive/
done
