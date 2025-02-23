#!/bin/bash
exec hypercorn app:app --bind 0.0.0.0:$PORT
