#!/usr/bin/env sh

image_tag=scraper
docker build -t $image_tag app

docker run --rm -it \
    -e TABLE_NAME=$TABLE_NAME \
    -e PARAMETER_NAME=$PARAMETER_NAME \
    -e AWS_DEFAULT_REGION=$REGION \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    -e ACCESS_TOKEN_PARAMETER_NAME=$ACCESS_TOKEN_PARAMETER_NAME \
    $image_tag
