import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ModulePlaceholderPage } from './pages/ModulePlaceholderPage';
import { NutritionDashboardPage } from './pages/nutrition/NutritionDashboardPage';
import { NutritionProfilePage } from './pages/nutrition/NutritionProfilePage';
import { MealPlanGeneratorPage } from './pages/nutrition/MealPlanGeneratorPage';
import { DailyMealPlanPage } from './pages/nutrition/DailyMealPlanPage';
import { FoodDetailPage } from './pages/nutrition/FoodDetailPage';
import { FoodDiaryPage } from './pages/nutrition/FoodDiaryPage';
import { NutritionProgressPage } from './pages/nutrition/NutritionProgressPage';
import { SafetyAlertPage } from './pages/nutrition/SafetyAlertPage';
import { AIExplanationPage } from './pages/nutrition/AIExplanationPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />

            {/* 9 Pages of Nutrition Recommendation Module */}
            <Route path="/nutrition" element={<NutritionDashboardPage />} />
            <Route path="/nutrition/profile" element={<NutritionProfilePage />} />
            <Route path="/nutrition/generate" element={<MealPlanGeneratorPage />} />
            <Route path="/nutrition/daily" element={<DailyMealPlanPage />} />
            <Route path="/nutrition/food/:foodId" element={<FoodDetailPage />} />
            <Route path="/nutrition/diary" element={<FoodDiaryPage />} />
            <Route path="/nutrition/progress" element={<NutritionProgressPage />} />
            <Route path="/nutrition/safety" element={<SafetyAlertPage />} />
            <Route path="/nutrition/explanation" element={<AIExplanationPage />} />

            {/* Other Global Shell Routes */}
            <Route
              path="/ai-consultation"
              element={
                <ModulePlaceholderPage
                  title="Tư vấn AI"
                  description="Hỏi đáp kiến thức đái tháo đường type 2 dựa trên RAG và nguồn y khoa chính thống"
                />
              }
            />
            <Route
              path="/exercise"
              element={
                <ModulePlaceholderPage
                  title="Luyện tập"
                  description="Giám sát tư thế tập luyện bằng AI Computer Vision (MediaPipe Pose)"
                />
              }
            />
            <Route
              path="/health-tracking"
              element={
                <ModulePlaceholderPage
                  title="Theo dõi sức khỏe"
                  description="Theo dõi chỉ số đường huyết và nhật ký sức khỏe tổng quát"
                />
              }
            />
            <Route
              path="/settings"
              element={
                <ModulePlaceholderPage
                  title="Cài đặt"
                  description="Quản lý tùy chọn tài khoản, thông báo và bảo mật"
                />
              }
            />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
