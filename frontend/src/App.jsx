import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'

import AppLayout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UsersPage from './pages/UsersPage'
import WorkflowsPage from './pages/WorkflowsPage'
import RayJobsPage from './pages/RayJobsPage'
import NotebooksPage from './pages/NotebooksPage'
import ProtectedRoute from './components/ProtectedRoute'

const { Content } = Layout

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/workflows" element={<WorkflowsPage />} />
                <Route path="/ray-jobs" element={<RayJobsPage />} />
                <Route path="/notebooks" element={<NotebooksPage />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App