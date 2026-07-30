@echo off

if not exist logs (
    mkdir logs
)

if not exist logs\mysql_setup.log (
    type nul > logs\mysql_setup.log
)

if not exist logs\mysql_load.log (
    type nul > logs\mysql_load.log
)