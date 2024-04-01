#!/bin/bash

sox "raw/$1" "bursts/$1" silence 1 0.1 1% 1 0.1 1% : newfile : restart
