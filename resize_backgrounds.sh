#!/usr/bin/env bash

cd assets/img/backgrounds

mkdir -p converted

find ./*.jpg -print0 | xargs -0 -I {} convert {} -sampling-factor 4:2:2 -strip -quality 90 -interlace JPEG -colorspace RGB -resize 480x800^ converted/{}