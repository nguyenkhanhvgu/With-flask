@echo off
REM Flask Blog Application Deployment Script for Windows
REM Usage: scripts\deploy.bat [environment] [action]
REM Environment: dev, staging, prod (default: dev)
REM Actions: deploy, stop, clean, backup, logs (default: deploy)

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

set ACTION=%2
if "%ACTION%"=="" set ACTION=deploy

set PROJECT_NAME=flask-blog

echo 🚀 Deploying Flask Blog Application - Environment: %ENVIRONMENT%

REM Check if Docker is installed and running
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Set compose file based on environment
if "%ENVIRONMENT%"=="prod" (
    if not exist ".env.prod" (
        echo [ERROR] Production environment file .env.prod not found!
        echo [WARNING] Please create .env.prod from .env.prod.example
        exit /b 1
    )
    set COMPOSE_FILE=docker-compose.prod.yml
) else (
    if not exist ".env" (
        echo [WARNING] Environment file .env not found. Creating from .env.example
        copy .env.example .env
    )
    set COMPOSE_FILE=docker-compose.yml
)

REM Execute action
if "%ACTION%"=="deploy" goto deploy
if "%ACTION%"=="stop" goto stop
if "%ACTION%"=="clean" goto clean
if "%ACTION%"=="backup" goto backup
if "%ACTION%"=="logs" goto logs
goto usage

:deploy
echo [INFO] Building Docker images...
docker-compose -f %COMPOSE_FILE% build --no-cache

echo [INFO] Starting services...
docker-compose -f %COMPOSE_FILE% up -d

echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo [INFO] Running database migrations...
docker-compose -f %COMPOSE_FILE% exec web flask db upgrade

echo [INFO] Checking service health...
docker-compose -f %COMPOSE_FILE% ps | findstr "Up" >nul
if errorlevel 1 (
    echo [ERROR] ❌ Deployment failed. Check logs with: docker-compose -f %COMPOSE_FILE% logs
    exit /b 1
) else (
    echo [INFO] ✅ Deployment successful!
    echo [INFO] Application is running at: http://localhost
    if "%ENVIRONMENT%"=="dev" (
        echo [INFO] Development services:
        echo [INFO]   - Web: http://localhost:5000
        echo [INFO]   - Database: localhost:5432
        echo [INFO]   - Redis: localhost:6379
    )
)
goto end

:stop
echo [INFO] Stopping services...
docker-compose -f %COMPOSE_FILE% down
goto end

:clean
echo [WARNING] Removing volumes (this will delete all data)...
docker-compose -f %COMPOSE_FILE% down -v
goto end

:backup
echo [INFO] Creating database backup...
set BACKUP_FILE=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
docker-compose -f %COMPOSE_FILE% exec db pg_dump -U bloguser blogdb > %BACKUP_FILE%
echo [INFO] Backup created: %BACKUP_FILE%
goto end

:logs
docker-compose -f %COMPOSE_FILE% logs -f
goto end

:usage
echo Usage: %0 [environment] [action]
echo Environment: dev, staging, prod (default: dev)
echo Actions: deploy, stop, clean, backup, logs (default: deploy)
exit /b 1

:end
endlocal