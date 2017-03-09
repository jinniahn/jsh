#!/bin/bash
echo -n "user_id: "
read user_id
# Read Password
echo -n "password: "
read -s password
echo
# Run Command
echo $user_id
echo $password
