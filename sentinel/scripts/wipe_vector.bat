@echo off
echo Wiping Long-term memory only...
rmdir /s /q "%USERPROFILE%\.sentinel\brain_vectors"
rmdir /s /q "%USERPROFILE%\.sentinel\.chroma"
del /f /q "%USERPROFILE%\.sentinel\memory.json"
echo Done.
exit