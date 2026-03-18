using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

class Program
{
    static void Main(string[] args)
    {
        int totalRecords = 0;
        int validRecords = 0;
        int duplicateRecords = 0;
        int rejectedRecords = 0;
        var seenPatientIds = new HashSet<string>();

        try
        {
            string inputJson = File.ReadAllText("/workspace/samples/patients.json");
            JsonDocument jsonDocument = JsonDocument.Parse(inputJson);
            JsonElement root = jsonDocument.RootElement;

            if (!root.ValueKind.Equals(JsonValueKind.Array))
            {
                throw new Exception("Invalid JSON array");
            }

            using (StreamWriter writer = new StreamWriter("/workspace/output/patients.ndjson"))
            {
                foreach (JsonElement element in root.EnumerateArray())
                {
                    totalRecords++;

                    if (!element.TryGetProperty("patient_id", out JsonElement patientIdElement) ||
                        patientIdElement.ValueKind != JsonValueKind.String ||
                        string.IsNullOrEmpty(patientIdElement.GetString()))
                    {
                        rejectedRecords++;
                        continue;
                    }

                    string patientId = patientIdElement.GetString();

                    if (seenPatientIds.Contains(patientId))
                    {
                        duplicateRecords++;
                        continue;
                    }

                    seenPatientIds.Add(patientId);

                    var patient = new Dictionary<string, object>
                    {
                        { "resourceType", "Patient" },
                        { "id", patientId },
                        { "identifier", new List<object>
                            {
                                new Dictionary<string, string>
                                {
                                    { "system", "urn:legacy:patient_id" },
                                    { "value", patientId }
                                }
                            }
                        }
                    };

                    if (element.TryGetProperty("first_name", out JsonElement firstNameElement) &&
                        firstNameElement.ValueKind == JsonValueKind.String &&
                        !string.IsNullOrEmpty(firstNameElement.GetString()))
                    {
                        string firstName = firstNameElement.GetString();

                        if (element.TryGetProperty("last_name", out JsonElement lastNameElement) &&
                            lastNameElement.ValueKind == JsonValueKind.String &&
                            !string.IsNullOrEmpty(lastNameElement.GetString()))
                        {
                            string lastName = lastNameElement.GetString();

                            patient.Add("name", new List<object>
                            {
                                new Dictionary<string, object>
                                {
                                    { "family", lastName },
                                    { "given", new List<string> { firstName } }
                                }
                            });
                        }
                        else
                        {
                            patient.Add("name", new List<object>
                            {
                                new Dictionary<string, object>
                                {
                                    { "given", new List<string> { firstName } }
                                }
                            });
                        }
                    }
                    else if (element.TryGetProperty("last_name", out JsonElement lastNameElement) &&
                               lastNameElement.ValueKind == JsonValueKind.String &&
                               !string.IsNullOrEmpty(lastNameElement.GetString()))
                    {
                        string lastName = lastNameElement.GetString();

                        patient.Add("name", new List<object>
                        {
                            new Dictionary<string, object>
                            {
                                { "family", lastName }
                            }
                        });
                    }

                    if (element.TryGetProperty("gender", out JsonElement genderElement) &&
                        genderElement.ValueKind == JsonValueKind.String)
                    {
                        string gender = genderElement.GetString().ToLower();

                        if (gender == "male" || gender == "female" || gender == "other" || gender == "unknown")
                        {
                            patient.Add("gender", gender);
                        }
                    }

                    if (element.TryGetProperty("birth_date", out JsonElement birthDateElement) &&
                        birthDateElement.ValueKind == JsonValueKind.String)
                    {
                        string birthDate = birthDateElement.GetString();

                        if (DateTime.TryParseExact(birthDate, new[] { "yyyy-MM-dd", "MM/dd/yyyy", "dd-MM-yyyy", "dd-MMM-yyyy" }, null, System.Globalization.DateTimeStyles.None, out DateTime parsedBirthDate))
                        {
                            patient.Add("birthDate", parsedBirthDate.ToString("yyyy-MM-dd"));
                        }
                    }

                    writer.WriteLine(JsonSerializer.Serialize(patient));
                    validRecords++;
                }
            }
        }
        catch (FileNotFoundException)
        {
            Console.WriteLine("Error: Input file not found.");
            return;
        }

        Console.WriteLine($"Total records: {totalRecords}");
        Console.WriteLine($"Valid records: {validRecords}");
        Console.WriteLine($"Duplicate records: {duplicateRecords}");
        Console.WriteLine($"Rejected records: {rejectedRecords}");
    }
}