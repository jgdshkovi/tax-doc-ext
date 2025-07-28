import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AdvancedUpload from './AdvancedUpload';
import AdvancedResults from './AdvancedResults';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AdvancedUpload />} />
        <Route path="/result" element={<AdvancedResults />} />
      </Routes>
    </Router>
  );
}

export default App;