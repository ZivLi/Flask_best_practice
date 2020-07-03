#!/bin/bash

if [ ! -d "$../.git/hooks/pre-push" ]
then
    cp pre-push ../.git/hooks/pre-push
    chmod +x ../.git/hooks/pre-push
    exit 0
fi

