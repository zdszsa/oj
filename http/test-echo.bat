@echo off
chcp 65001 >nul
set BASE=http://localhost:8080

echo ============================================
echo   Case 1  {"text":"hi"}          normal
echo   expect  HTTP 200 + hi
echo ============================================
curl -s -i -X POST -H "Content-Type: application/json" -d "@%~dp01-ok.json" %BASE%/echo
echo.
echo.

echo ============================================
echo   Case 2  {"text":""}            empty string
echo   expect  HTTP 200 + error message, NOT 500
echo ============================================
curl -s -i -X POST -H "Content-Type: application/json" -d "@%~dp04-empty-text.json" %BASE%/echo
echo.
echo.

echo ============================================
echo   Case 3  {"message":"hi"}       wrong key
echo   expect  HTTP 200 + error message, NOT 500
echo ============================================
curl -s -i -X POST -H "Content-Type: application/json" -d "@%~dp02-wrong-key.json" %BASE%/echo
echo.
echo.

echo ============================================
echo   Case 4  {}                    empty body
echo   expect  HTTP 200 + error message, NOT 500
echo ============================================
curl -s -i -X POST -H "Content-Type: application/json" -d "@%~dp05-empty-json.json" %BASE%/echo
echo.
echo.

echo ============================================
echo   Case 5  {"text":"line1\nline2\nline3"}
echo   expect  HTTP 200 + 3 real lines
echo ============================================
curl -s -i -X POST -H "Content-Type: application/json" -d "@%~dp03-multiline.json" %BASE%/echo
echo.
echo.

echo ============================================
echo   PASS means:
echo     Case 1            -> hi
echo     Case 2, 3, 4      -> the error message, all HTTP 200
echo     Case 5            -> 3 separate lines
echo   Nothing at all means the app is not on 8080.
echo ============================================
pause
