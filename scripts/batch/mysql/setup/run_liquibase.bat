REM =====================================
REM CLEAR LIQUIBASE CHECKSUMS
REM =====================================

echo.
echo =====================================
echo CLEARING LIQUIBASE CHECKSUMS
echo =====================================
echo.

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.mysql.cj.jdbc.Driver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:mysql://%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%" ^
--username=%MYSQL_USER% ^
%PASSWORD_OPTION% ^
clearCheckSums

if errorlevel 1 (

echo.
echo ERROR: LIQUIBASE CLEAR CHECKSUMS FAILED
exit /b 1

)

REM =====================================
REM RUN LIQUIBASE UPDATE
REM =====================================

echo.
echo =====================================
echo RUNNING LIQUIBASE UPDATE
echo =====================================
echo.

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.mysql.cj.jdbc.Driver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:mysql://%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%" ^
--username=%MYSQL_USER% ^
%PASSWORD_OPTION% ^
update

if errorlevel 1 (

echo.
echo ERROR: LIQUIBASE UPDATE FAILED
exit /b 1

)