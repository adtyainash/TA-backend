import './App.css'
import { Link } from 'react-router'

function App() {
  return (
    <div className="app">
      <nav>
        <Link to="/submitcase">
          <button>Submit Diagnosa</button>
        </Link>
      </nav>
      <header className="header">
        <h1>Dashboard DBD</h1>
      </header>
      <main className="main-content">
        <div className="dashboard-section">
          <div className="dashboard-container">
            <iframe 
              title="Dashboard DBD" 
              width="100%" 
              height="1000" 
              src="https://app.powerbi.com/view?r=eyJrIjoiOTZjMDM3YTAtNmI2Yy00NTg1LTkzNWEtYTQ4MWJmNzMzZDUxIiwidCI6ImRiNmUxMTgzLTRjNjUtNDA1Yy04MmNlLTdjZDUzZmE2ZTlkYyIsImMiOjEwfQ%3D%3D" 
              frameBorder="0" 
              allowFullScreen={true}
            />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
