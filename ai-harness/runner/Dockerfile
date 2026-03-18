FROM mcr.microsoft.com/dotnet/sdk:8.0

WORKDIR /workspace/generated

COPY run_pipeline.sh /run_pipeline.sh
RUN chmod +x /run_pipeline.sh

CMD ["tail", "-f", "/dev/null"]