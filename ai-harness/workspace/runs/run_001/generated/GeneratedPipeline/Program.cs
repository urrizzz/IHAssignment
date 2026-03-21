using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

class Program
{
    static void Main()
    {
        string inputPath = "/workspace/samples/patients.json";
        string outputPath = "/workspace/output/patients.ndjson";

        if (!File.Exists(inputPath))
        {
            Console.WriteLine("Error: Input file not found.");
            return;
        }

        string json = File.ReadAllText(inputPath);
        JsonDocument doc = JsonDocument.Parse(json);
        JsonElement root = doc.RootElement;

        int totalRecords = 0;
        int validRecords = 0;
        int duplicateRecords = 0;
        int rejectedRecords = 0;

        HashSet<string> patientIds = new HashSet<string>();

        if (!Directory.Exists("/workspace/output"))
        {
            Directory.CreateDirectory("/workspace/output");
        }

        using (StreamWriter writer = new StreamWriter(outputPath))
        {
            foreach (JsonElement element in root.EnumerateArray())
            {
                totalRecords++;

                if (element.TryGetProperty("patient_id", out JsonElement patientId) && patientId.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(patientId.GetString()))
                {
                    string patientIdValue = patientId.GetString();

                    if (patientIds.Contains(patientIdValue))
                    {
                        duplicateRecords++;
                    }
                    else
                    {
                        patientIds.Add(patientIdValue);

                        Dictionary<string, object> patient = new Dictionary<string, object>
                        {
                            { "resourceType", "Patient" },
                            { "id", patientIdValue },
                            { "identifier", new List<object> { new Dictionary<string, object> { { "system", "urn:legacy:patient_id" }, { "value", patientIdValue } } } }
                        };

                        if (element.TryGetProperty("first_name", out JsonElement firstName) && firstName.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(firstName.GetString()))
                        {
                            string firstNameValue = firstName.GetString();

                            if (element.TryGetProperty("last_name", out JsonElement lastName) && lastName.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(lastName.GetString()))
                            {
                                string lastNameValue = lastName.GetString();

                                patient["name"] = new List<object> { new Dictionary<string, object> { { "family", lastNameValue }, { "given", new List<object> { firstNameValue } } } };
                            }
                            else
                            {
                                patient["name"] = new List<object> { new Dictionary<string, object> { { "given", new List<object> { firstNameValue } } } };
                            }
                        }
                        else if (element.TryGetProperty("last_name", out JsonElement lastName) && lastName.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(lastName.GetString()))
                        {
                            string lastNameValue = lastName.GetString();

                            patient["name"] = new List<object> { new Dictionary<string, object> { { "family", lastNameValue } } };
                        }

                        if (element.TryGetProperty("gender", out JsonElement gender) && gender.ValueKind == JsonValueKind.String)
                        {
                            string genderValue = gender.GetString().ToLower();

                            if (genderValue == "male" || genderValue == "female" || genderValue == "other" || genderValue == "unknown")
                            {
                                patient["gender"] = genderValue;
                            }
                        }

                        if (element.TryGetProperty("birth_date", out JsonElement birthDate) && birthDate.ValueKind == JsonValueKind.String)
                        {
                            string birthDateValue = birthDate.GetString();

                            if (DateTime.TryParseExact(birthDateValue, new[] { "yyyy-MM-dd", "MM/dd/yyyy", "dd-MM-yyyy", "dd-MMM-yyyy" }, null, System.Globalization.DateTimeStyles.None, out DateTime birthDateParsed))
                            {
                                patient["birthDate"] = birthDateParsed.ToString("yyyy-MM-dd");
                            }
                        }

                        writer.WriteLine(JsonSerializer.Serialize(patient));
                        validRecords++;
                    }
                }
                else
                {
                    rejectedRecords++;
                }
            }
        }

        Console.WriteLine($"Total records: {totalRecords}");
        Console.WriteLine($"Valid records: {validRecords}");
        Console.WriteLine($"Duplicate records: {duplicateRecords}");
        Console.WriteLine($"Rejected records: {rejectedRecords}");
    }
}