import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '../components/AppLayout';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { DigestPreviewPage } from '../features/digest/DigestPreviewPage';
import { EmailsPage } from '../features/emails/EmailsPage';
import { PlacesPage } from '../features/places/PlacesPage';
import { QuizPage } from '../features/quiz/QuizPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { StudyPlanPage } from '../features/study/StudyPlanPage';
import { SummarizePage } from '../features/summarize/SummarizePage';
import { TodoPage } from '../features/todo/TodoPage';
import { TravelPage } from '../features/travel/TravelPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="emails" element={<EmailsPage />} />
        <Route path="study/plan" element={<StudyPlanPage />} />
        <Route path="summarize" element={<SummarizePage />} />
        <Route path="quiz" element={<QuizPage />} />
        <Route path="travel" element={<TravelPage />} />
        <Route path="todo" element={<TodoPage />} />
        <Route path="places" element={<PlacesPage />} />
        <Route path="digest/preview" element={<DigestPreviewPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
