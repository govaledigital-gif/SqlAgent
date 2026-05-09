import React from 'react';
import SqlGenerator from './components/SqlGenerator';
import SqlController from './controllers/SqlController';
import './App.css';

function App() {
  const sqlController = SqlController();

  return (
    <div className="App">
      <SqlGenerator controller={sqlController} />
    </div>
  );
}

export default App;
