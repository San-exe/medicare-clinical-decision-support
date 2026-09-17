import React from "react";
import { Route, Routes, Navigate } from "react-router-dom";

import DoctorDashboard from "./doctor_dashboard";
import Patients from "./patients";
import Reports from "./reports";
import Insights from "./insights";
import ClinicalNotes from "./clinicalnotes";
import MedicalKnowledge from "./medknowledge";
import Settings from "./settings";
import Logout from "./logout";
import Appointments from "./appointmentss";

export default function DoctorRoutes() {
  return (
    <Routes>
      <Route path="/doctor" element={<Navigate to="/doctor/dashboard" replace />} />
      <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
      <Route path="/doctor/patients" element={<Patients />} />
      <Route path="/doctor/reports" element={<Reports />} />
      <Route path="/doctor/insights" element={<Insights />} />
      <Route path="/doctor/appointments" element={<Appointments />} />
      <Route path="/doctor/clinical-notes" element={<ClinicalNotes />} />
      <Route path="/doctor/medical-knowledge" element={<MedicalKnowledge />} />
      <Route path="/doctor/settings" element={<Settings />} />
      <Route path="/doctor/logout" element={<Logout />} />
    </Routes>
  );
}
