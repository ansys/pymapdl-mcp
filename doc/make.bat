@ECHO OFF
REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set BUILDDIR=_build
set ALLSPHINXOPTS=-W --keep-going -d %BUILDDIR%/doctrees %SPHINXOPTS% source
if not "%PAPER%" == "" (
	set ALLSPHINXOPTS=-D latex_paper_size=%PAPER% %ALLSPHINXOPTS%
)

if "%1" == "" goto help

if "%1" == "clean" (
	for /d %%i in (%BUILDDIR%\*) do (rmdir /s /q "%%i")
	if exist %BUILDDIR% rmdir /s /q %BUILDDIR%
	goto end
)

if "%1" == "html" (
	%SPHINXBUILD% -b html %ALLSPHINXOPTS% %BUILDDIR%/html
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILDDIR%/html.
	goto end
)

:help
%SPHINXBUILD% -M help %ALLSPHINXOPTS% %BUILDDIR%
goto end

:end
