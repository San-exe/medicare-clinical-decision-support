// Frontend demonstration data only. Replace these exports with API service calls when the Django REST endpoints are available.

export const patientProfile = {
  name: "John Doe",
  age: 34,
  gender: "Male",
  bloodType: "O+",
  height: "5'10\"",
  weight: "165 lb",
  email: "john.doe@example.com",
  phone: "+1 (555) 014-0172",
  dateOfBirth: "1992-04-18",
};

export const dashboardMetrics = [
  { label: "Blood Pressure", value: "120/80", unit: "mmHg", status: "Normal" },
  { label: "Temperature", value: "98.6", unit: "°F", status: "Normal" },
  { label: "Oxygen Level", value: "97", unit: "%", status: "Normal" },
  { label: "Resting Heart Rate", value: "72", unit: "bpm", status: "Normal" },
];

export const bloodPressureData = [
  { day: "May 16", systolic: 120, diastolic: 78 },
  { day: "May 17", systolic: 117, diastolic: 77 },
  { day: "May 18", systolic: 125, diastolic: 83 },
  { day: "May 19", systolic: 112, diastolic: 79 },
  { day: "May 20", systolic: 118, diastolic: 79 },
  { day: "May 21", systolic: 124, diastolic: 83 },
  { day: "May 22", systolic: 118, diastolic: 78 },
];

export const trendData = [
  { date: "May 16", heartRate: 74, glucose: 93, weight: 166, systolic: 120, diastolic: 78 },
  { date: "May 17", heartRate: 72, glucose: 95, weight: 165.8, systolic: 117, diastolic: 77 },
  { date: "May 18", heartRate: 76, glucose: 91, weight: 165.6, systolic: 125, diastolic: 83 },
  { date: "May 19", heartRate: 70, glucose: 90, weight: 165.4, systolic: 112, diastolic: 79 },
  { date: "May 20", heartRate: 71, glucose: 94, weight: 165.2, systolic: 118, diastolic: 79 },
  { date: "May 21", heartRate: 73, glucose: 92, weight: 165, systolic: 124, diastolic: 83 },
  { date: "May 22", heartRate: 72, glucose: 89, weight: 164.8, systolic: 118, diastolic: 78 },
];

export const appointments = [
  { id: "a1", doctor: "Dr. Sarah Mitchell", specialty: "Primary Care", date: "May 28, 2026", time: "10:30 AM", location: "Green Valley Clinic · Room 204", status: "Scheduled", notes: "Routine wellness follow-up" },
  { id: "a2", doctor: "Dr. Michael Chen", specialty: "Cardiology", date: "Jun 12, 2026", time: "2:00 PM", location: "Green Valley Clinic · Room 108", status: "Scheduled", notes: "Review blood pressure history" },
  { id: "a3", doctor: "Dr. Sarah Mitchell", specialty: "Primary Care", date: "Apr 15, 2026", time: "9:00 AM", location: "Green Valley Clinic · Room 204", status: "Completed", notes: "Annual check-in" },
  { id: "a4", doctor: "Dr. Priya Patel", specialty: "Dermatology", date: "Mar 04, 2026", time: "11:00 AM", location: "Green Valley Clinic · Room 312", status: "Cancelled", notes: "Patient requested cancellation" },
];

export const medicalRecords = [
  { id: "r1", name: "Annual wellness summary", type: "Doctor Notes", doctor: "Dr. Sarah Mitchell", date: "Apr 15, 2026", size: "482 KB" },
  { id: "r2", name: "Complete blood count", type: "Lab Reports", doctor: "Green Valley Lab", date: "Apr 15, 2026", size: "1.2 MB" },
  { id: "r3", name: "Medication renewal", type: "Prescriptions", doctor: "Dr. Sarah Mitchell", date: "Mar 21, 2026", size: "214 KB" },
  { id: "r4", name: "Chest imaging report", type: "Imaging", doctor: "Green Valley Radiology", date: "Feb 08, 2026", size: "2.8 MB" },
];

export const labTests = [
  { id: "l1", test: "Fasting glucose", result: "89 mg/dL", reference: "70–99 mg/dL", status: "Normal", date: "Apr 15, 2026", previous: "92 mg/dL", trend: "Improving" },
  { id: "l2", test: "Hemoglobin", result: "14.2 g/dL", reference: "13.5–17.5 g/dL", status: "Normal", date: "Apr 15, 2026", previous: "14.0 g/dL", trend: "Stable" },
  { id: "l3", test: "Total cholesterol", result: "204 mg/dL", reference: "<200 mg/dL", status: "Abnormal", date: "Apr 15, 2026", previous: "198 mg/dL", trend: "Review" },
  { id: "l4", test: "Vitamin D", result: "Pending", reference: "30–100 ng/mL", status: "Pending", date: "Apr 15, 2026", previous: "—", trend: "Pending" },
];

export const medications = [
  { id: "m1", name: "Lisinopril", generic: "Lisinopril", dose: "10 mg", frequency: "Once daily", schedule: "8:00 AM", doctor: "Dr. Michael Chen", start: "Jan 12, 2026", refill: "18 days left", status: "Active" },
  { id: "m2", name: "Vitamin D3", generic: "Cholecalciferol", dose: "1,000 IU", frequency: "Once daily", schedule: "8:00 AM", doctor: "Dr. Sarah Mitchell", start: "Feb 02, 2026", refill: "42 days left", status: "Active" },
  { id: "m3", name: "Cetirizine", generic: "Cetirizine hydrochloride", dose: "10 mg", frequency: "As needed", schedule: "Evening", doctor: "Dr. Sarah Mitchell", start: "Mar 18, 2026", refill: "7 tablets left", status: "Active" },
];

export const medicationSchedule = [
  { time: "8:00 AM", medicine: "Lisinopril", dose: "10 mg", status: "Taken" },
  { time: "8:00 AM", medicine: "Vitamin D3", dose: "1,000 IU", status: "Taken" },
  { time: "8:00 PM", medicine: "Cetirizine", dose: "10 mg", status: "Not taken" },
];

export const predictionCards = [
  { id: "p1", name: "Cardiometabolic health", confidence: 42, level: "Lower signal", factors: ["Blood pressure history", "Recent glucose readings", "Activity trend"], explanation: "A frontend placeholder for future model-provided explanations." },
  { id: "p2", name: "Glucose regulation", confidence: 27, level: "Lower signal", factors: ["Fasting glucose trend", "Weight trend", "Family history input"], explanation: "No clinical prediction has been run in this demo." },
  { id: "p3", name: "Sleep recovery", confidence: 61, level: "Review context", factors: ["Reported fatigue", "Resting heart rate", "Sleep duration input"], explanation: "This card illustrates where a future explainability payload can appear." },
];

export const medicineCatalog = [
  { id: "d1", name: "Lisinopril", generic: "Lisinopril", category: "Cardiovascular", summary: "Example medicine profile ready for an OpenFDA or DrugBank response.", uses: "Blood pressure management", dosage: "Use only the dose prescribed by a clinician.", contraindications: "Check allergies, pregnancy status, kidney history, and current medicines with a clinician.", sideEffects: "A connected source should provide current side-effect information.", warnings: "Do not change or stop treatment without professional guidance.", interactions: "Review with the interaction checker and a pharmacist." },
  { id: "d2", name: "Metformin", generic: "Metformin hydrochloride", category: "Diabetes", summary: "Example search result; clinical details require an authoritative connected source.", uses: "Diabetes-care information placeholder", dosage: "Follow the prescribed label and clinician instructions.", contraindications: "Confirm suitability with a clinician who knows your history.", sideEffects: "Authoritative source data should be shown here.", warnings: "Seek professional guidance for changes or concerning symptoms.", interactions: "Review all medicines, supplements, and alcohol use with a pharmacist." },
  { id: "d3", name: "Cetirizine", generic: "Cetirizine hydrochloride", category: "Allergy", summary: "Example medicine profile for the search experience.", uses: "Allergy-information placeholder", dosage: "Follow the package label or clinician instructions.", contraindications: "Check personal conditions and other medicines with a clinician.", sideEffects: "Connected medicine data should populate this section.", warnings: "Use safety information from the connected medicine source.", interactions: "Review possible interactions before combining medicines." },
];

export const symptomSuggestions = ["Headache", "Fatigue", "Fever", "Nausea", "Cough", "Dizziness", "Sore throat", "Back pain"];

export const predictionHistory = [
  { date: "Apr 15, 2026", label: "Routine health review", status: "Completed" },
  { date: "Jan 12, 2026", label: "Baseline assessment", status: "Completed" },
];
