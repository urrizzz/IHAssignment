Generate a .NET 8 console application in a single Program.cs file.

Goal:
Read a JSON array from /workspace/samples/patients.json, validate and deduplicate records by patient_id, transform valid records into minimal FHIR Patient JSON resources, and write them as NDJSON to /workspace/output/patients.ndjson.

Critical implementation pattern:
- Keep the implementation simple and deterministic
- Use only standard .NET libraries
- Do not use external packages
- Do not use any FHIR library
- Build each output record using Dictionary<string, object>
- Build arrays using List<object>
- Serialize each completed output record using JsonSerializer.Serialize
- Write exactly one serialized JSON object per line to the output file

Critical JSON safety rules:
- Do NOT call GetProperty on optional fields unless you first know the property exists
- Use TryGetProperty for patient_id, first_name, last_name, gender, and birth_date
- Do NOT call GetString() unless the JsonElement ValueKind is String
- Do NOT compare JsonElement directly to null
- For required validation, use TryGetProperty plus ValueKind checks
- The program must not throw if a property is missing, null, numeric, boolean, object, or array
- Invalid or unexpected field types must be handled safely by rejecting the record only when patient_id is invalid, or omitting optional fields otherwise

Input parsing:
- Read input ONLY from:
  /workspace/samples/patients.json
- The input file is one JSON array, not NDJSON
- Read the full file as one string
- Parse the full file as a JSON array using JsonDocument.Parse
- If the input file does not exist, print exactly:
  Error: Input file not found.
- Then exit

Output:
- Write output ONLY to:
  /workspace/output/patients.ndjson
- Ensure the parent directory /workspace/output exists before writing
- Overwrite the output file on each run
- The output file must contain NDJSON only
- NDJSON means exactly one valid JSON object per line
- Do not write blank lines
- Do not write logging text into the output file

FHIR Patient output:
- Each valid output line must be one JSON object
- Each output object must contain:
  - resourceType = "Patient"
  - identifier = array with one object:
    - system = "urn:legacy:patient_id"
    - value = source patient_id
- If first_name and/or last_name are present and are non-empty strings, include:
  - name = array with one object
- In that name object:
  - include family only if last_name is a non-empty string
  - include given only if first_name is a non-empty string
  - given must be an array containing the first_name string
- If gender is present as a string and normalizes to one of:
  - male
  - female
  - other
  - unknown
  then include gender as that lowercase string
- If birth_date is present as a string and parseable, include birthDate in yyyy-MM-dd format
- If birth_date is missing, null, non-string, or invalid, omit birthDate
- Do not reject the record because of invalid or missing first_name, last_name, gender, or birth_date
- Do not include unsupported fields

Additional FHIR requirement:
- Each Patient resource MUST include an "id" field
- The "id" value MUST be exactly equal to patient_id
- The identifier array MUST still include:
  - system = "urn:legacy:patient_id"
  - value = patient_id
- The "id" field and identifier[0].value MUST match exactly

Validation and deduplication:
- Validate only patient_id as required
- Reject a record if patient_id is:
  - missing
  - null
  - not a JSON string
  - an empty string
- Do not assume patient_id exists
- Do not assume patient_id is a string
- Deduplicate by patient_id
- Keep only the first valid occurrence
- Count later valid occurrences of the same patient_id as duplicates
- Continue processing even if some records are invalid

Date handling:
- Support these input birth_date formats if possible:
  - yyyy-MM-dd
  - MM/dd/yyyy
  - dd-MM-yyyy
  - dd-MMM-yyyy
- Normalize parsed birth_date values to yyyy-MM-dd
- If parsing fails, omit birthDate and continue

Counts:
- Total records = number of objects in the input array
- Valid records = records written to output
- Duplicate records = later records skipped because patient_id was already seen
- Rejected records = records skipped because patient_id is invalid

Console output:
Print exactly these four lines and nothing else:
Total records: <number>
Valid records: <number>
Duplicate records: <number>
Rejected records: <number>

Technical constraints:
- Single Program.cs only
- Return compilable code only
- No explanations
- No markdown fences
- No undefined types
- No code that depends on unavailable libraries
- If helper methods are used, define them in the same Program.cs file