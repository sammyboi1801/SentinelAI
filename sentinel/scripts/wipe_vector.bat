@echo off
echo Wiping Long-term memory only...
rmdir /s /q "%USERPROFILE%\.sentinel-1\brain_vectors"
rmdir /s /q "%USERPROFILE%\.sentinel-1\.chroma"
del /f /q "%USERPROFILE%\.sentinel-1\memory.json"
echo Done.
exit