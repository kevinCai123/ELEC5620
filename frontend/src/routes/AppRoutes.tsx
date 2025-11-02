import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '../components/AppLayout';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { LoginPage } from '../features/auth/LoginPage';
import { CodeGenerationPage } from '../features/code/CodeGenerationPage';
import { CodeSandboxPage } from '../features/code/CodeSandboxPage';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { DigestPreviewPage } from '../features/digest/DigestPreviewPage';
import { EmailsPage } from '../features/emails/EmailsPage';
import { PlacesPage } from '../features/places/PlacesPage';
import { PlanPage } from '../features/plan/PlanPage';
import { QuizPage } from '../features/quiz/QuizPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { SummarizePage } from '../features/summarize/SummarizePage';
import { TravelPage } from '../features/travel/TravelPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Root redirects to login */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* Login page */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="emails" element={<EmailsPage />} />
        <Route path="plan" element={<PlanPage />} />
        <Route path="study/plan" element={<Navigate to="/plan" replace />} />
        <Route path="summarize" element={<SummarizePage />} />
        <Route path="quiz" element={<QuizPage />} />
        <Route path="code/generate" element={<CodeGenerationPage />} />
        <Route path="code/sandbox" element={<CodeSandboxPage />} />
        <Route path="travel" element={<TravelPage />} />
        <Route path="places" element={<PlacesPage />} />
        <Route path="digest/preview" element={<DigestPreviewPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
