Requrements:
* project can run on linux/windows
* the host machine needs Docker/Compose to be installed
* the \ai-harness\workspace folder is mapped to directly to both work containers

To run:
* go to \ai-harness folder
* docker compose up -d 
* 2 container are goign to be built, takes some time first run
* this will start 2 container, "ai-harness" and "dotnet-runner"
* "dot-netrunner" is always runnig, ai-harness triggers "build" and "run" commands
* "ai-harness" executes the current workflow from json file \ai-harness\workspace\workflows\patient_import_v3.json
* "ai-harness" container is shut down after execution
* execution artefacts are created in \workspace\runs (code, logs, metadata, generated prompts, steps metadata)
* sample input data is in \workspace\samples
* generated output file is in \workspace\output
* promts used on all teps are in \workspace\tasks
* after analysing results and makng changes in workflow, prompts, samples the harness container can be restarted:
* docker compose up --build harness

Additional info:
* \ai-harness needs .env file with API key to connect to GROQ
GROQ_API_KEY=<API_KEY> 
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
* model in .env file is default model, it can be defined for every AI step in workflow json
* if you use free dev access to GROQ it is suggested to use different model on every step to avoid hitting the usage limits
* workflow json file is hardcoded
* the \workspace\runs artifacts are cleared before every run and only the last iteration artifacts are preserved, versioning of artifacts is not implemented EXCEPT prompt versions (implementation is hardcoded, so better general soltuion needed here)