@echo off
REM Flask Blog Development Helper Script for Windows
REM Provides common development tasks for Docker environment

setlocal enabledelayedexpansion

set COMMAND=%1
set OPTION=%2

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    if not "%COMMAND%"=="status" (
        echo [ERROR] Services are not running. Start them with: scripts\deploy.bat dev
        exit /b 1
    )
)

REM Development commands
if "%COMMAND%"=="shell" goto shell
if "%COMMAND%"=="db-shell" goto db-shell
if "%COMMAND%"=="redis-shell" goto redis-shell
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="migrate" goto migrate
if "%COMMAND%"=="upgrade" goto upgrade
if "%COMMAND%"=="downgrade" goto downgrade
if "%COMMAND%"=="test" goto test
if "%COMMAND%"=="lint" goto lint
if "%COMMAND%"=="format" goto format
if "%COMMAND%"=="seed" goto seed
if "%COMMAND%"=="clean" goto clean
if "%COMMAND%"=="rebuild" goto rebuild
if "%COMMAND%"=="status" goto status
goto usage

:shell
echo === Opening Flask Application Shell ===
docker-compose exec web flask shell
goto end

:db-shell
echo === Opening Database Shell ===
docker-compose exec db psql -U bloguser -d blogdb
goto end

:redis-shell
echo === Opening Redis Shell ===
docker-compose exec redis redis-cli
goto end

:logs
if "%OPTION%"=="" set OPTION=web
echo === Showing logs for service: %OPTION% ===
docker-compose logs -f %OPTION%
goto end

:migrate
if "%OPTION%"=="" set OPTION=Auto migration
echo === Running Database Migration ===
docker-compose exec web flask db migrate -m "%OPTION%"
goto end

:upgrade
echo === Upgrading Database ===
docker-compose exec web flask db upgrade
goto end

:downgrade
echo === Downgrading Database ===
docker-compose exec web flask db downgrade
goto end

:test
if "%OPTION%"=="" set OPTION=tests/
echo === Running Tests ===
docker-compose exec web python -m pytest %OPTION% -v
goto end

:lint
echo === Running Code Linting ===
docker-compose exec web flake8 app/ --max-line-length=120
goto end

:format
echo === Formatting Code ===
docker-compose exec web black app/ --line-length=120
goto end

:seed
echo === Seeding Database with Sample Data ===
docker-compose exec web python -c "from app import create_app, db; from app.models import User, Post, Category; import os; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@example.com') if not User.query.filter_by(username='admin').first() else None; admin.set_password('admin123') if admin else None; admin.is_admin = True if admin else None; db.session.add(admin) if admin else None; tech_cat = Category(name='Technology', description='Tech posts') if not Category.query.filter_by(name='Technology').first() else None; db.session.add(tech_cat) if tech_cat else None; db.session.commit(); print('Sample data created successfully!')"
goto end

:clean
echo === Cleaning Development Environment ===
docker-compose down
docker system prune -f
docker volume prune -f
goto end

:rebuild
echo === Rebuilding Services ===
docker-compose down
docker-compose build --no-cache
docker-compose up -d
goto end

:status
echo === Service Status ===
docker-compose ps
echo.
echo [INFO] Service URLs:
echo [INFO]   Web Application: http://localhost:5000
echo [INFO]   Database: localhost:5432
echo [INFO]   Redis: localhost:6379
echo [INFO]   Nginx: http://localhost
goto end

:usage
echo Flask Blog Development Helper
echo.
echo Usage: %0 ^<command^> [options]
echo.
echo Commands:
echo   shell              Open Flask application shell
echo   db-shell           Open database shell (psql)
echo   redis-shell        Open Redis shell
echo   logs [service]     Show logs (default: web)
echo   migrate [message]  Create new database migration
echo   upgrade            Apply database migrations
echo   downgrade          Rollback database migration
echo   test [path]        Run tests (default: all tests)
echo   lint               Run code linting
echo   format             Format code with black
echo   seed               Seed database with sample data
echo   clean              Clean development environment
echo   rebuild            Rebuild and restart services
echo   status             Show service status and URLs
echo.
echo Examples:
echo   %0 shell
echo   %0 logs web
echo   %0 migrate "Add user roles"
echo   %0 test tests/unit/
exit /b 1

:end
endlocal