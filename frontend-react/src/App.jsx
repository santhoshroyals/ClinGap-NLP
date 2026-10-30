import React from 'react';
import { AnalysisProvider, useAnalysis } from './context/AnalysisContext';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ClinicalInputPage } from './pages/ClinicalInputPage';
import { EntityExtractionPage } from './pages/EntityExtractionPage';
import { GuidelineMatchingPage } from './pages/GuidelineMatchingPage';
import { GapDetectionPage } from './pages/GapDetectionPage';
import { PrescriptionPage } from './pages/PrescriptionPage';
import { TimelinePage } from './pages/TimelinePage';
import { AboutPage } from './pages/AboutPage';

function PageRouter() {
  const { activeTab } = useAnalysis();

  switch (activeTab) {
    case 'dashboard':
      return <DashboardPage />;
    case 'input':
      return <ClinicalInputPage />;
    case 'entities':
      return <EntityExtractionPage />;
    case 'guidelines':
      return <GuidelineMatchingPage />;
    case 'gaps':
      return <GapDetectionPage />;
    case 'prescriptions':
      return <PrescriptionPage />;
    case 'timeline':
      return <TimelinePage />;
    case 'about':
      return <AboutPage />;
    default:
      return <DashboardPage />;
  }
}

export default function App() {
  return (
    <AnalysisProvider>
      <Layout>
        <PageRouter />
      </Layout>
    </AnalysisProvider>
  );
}
