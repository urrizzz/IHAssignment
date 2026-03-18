#!/bin/sh
set -e

echo "Starting .NET pipeline run..." | tee -a /logs/dotnet-runner.log

PROJECT=$(find /workspace/generated -name "*.csproj" | head -n 1)

if [ -z "$PROJECT" ]; then
  echo "No .NET project found in /workspace/generated" | tee -a /logs/dotnet-runner.log
  exit 1
fi

echo "Using project: $PROJECT"

dotnet restore "$PROJECT" | tee -a /logs/dotnet-runner.log
dotnet build "$PROJECT" | tee -a /logs/dotnet-runner.log
dotnet run --project "$PROJECT" | tee -a /logs/dotnet-runner.log