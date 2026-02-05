@echo off
title Sentinel Factory Reset

echo.
echo !!! THIS WILL DELETE ALL SENTINEL DATA !!!
echo Location:
echo %USERPROFILE%\.sentinel
echo.
pause

rmdir /s /q "%USERPROFILE%\.sentinel"
mkdir "%USERPROFILE%\.sentinel"

echo.
echo Sentinel has been FACTORY RESET.
echo All memory, vectors, tokens, logs deleted.
exit