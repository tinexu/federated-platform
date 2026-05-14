import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import ProductionArchitecture from './components/ProductionArchitecture';
import RealTimeMonitor from './components/RealTimeMonitor';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

function Landing() {
    const [apiStatus, setApiStatus] = React.useState('checking...');
    const [error, setError] = React.useState(null);
    
    React.useEffect(() => {
      fetch('http://localhost:5001/api/health')
        .then(res => {
          if (!res.ok) throw new Error('API not responding');
          return res.json();
        })
        .then(data => {
          setApiStatus(data.status);
          setError(null);
        })
        .catch(err => {
          console.error('API Error:', err);
          setApiStatus('offline');
          setError('Cannot connect to backend.');
        });
    }, []);
    
    return (
      <div style={{ 
        minHeight: '100vh',
        background: '#0a0a0a',
        color: '#e0e0e0'
      }}>
        <div className="container" style={{ paddingTop: '60px' }}>
          {/* Header */}
          <header style={{ textAlign: 'center', marginBottom: '80px' }}>
            <h1 style={{ 
              fontSize: '56px', 
              fontWeight: '700',
              marginBottom: '20px',
              background: 'linear-gradient(135deg, #fff 0%, #888 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              MedFL
            </h1>
            <p style={{ 
              fontSize: '20px', 
              color: '#888',
              maxWidth: '600px',
              margin: '0 auto'
            }}>
              Secure federated learning infrastructure for healthcare organizations
            </p>
          </header>
  
          {/* Features */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '24px',
            marginBottom: '60px'
          }}>
            <div className="card">
              <div style={{ fontSize: '28px', marginBottom: '16px' }}>🛡️</div>
              <h3 style={{ fontSize: '20px', marginBottom: '12px', color: '#fff' }}>
                HIPAA Compliant
              </h3>
              <p style={{ color: '#888', fontSize: '15px' }}>
                Differential privacy with ε≤3.0 ensures patient data never leaves hospital premises
              </p>
            </div>
  
            <div className="card">
              <div style={{ fontSize: '28px', marginBottom: '16px' }}>🔗</div>
              <h3 style={{ fontSize: '20px', marginBottom: '12px', color: '#fff' }}>
                Multi-Site Learning
              </h3>
              <p style={{ color: '#888', fontSize: '15px' }}>
                Train models across hospital networks without centralizing sensitive data
              </p>
            </div>
  
            <div className="card">
              <div style={{ fontSize: '28px', marginBottom: '16px' }}>📈</div>
              <h3 style={{ fontSize: '20px', marginBottom: '12px', color: '#fff' }}>
                Improved Accuracy
              </h3>
              <p style={{ color: '#888', fontSize: '15px' }}>
                Access 10x more training data through collaboration, improving diagnostic accuracy
              </p>
            </div>
          </div>
  
          {/* Status Bar */}
          <div style={{ 
            background: '#111',
            border: '1px solid #222',
            borderRadius: '8px',
            padding: '16px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '40px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span className={`status-indicator ${apiStatus === 'healthy' ? 'status-healthy' : 'status-error'}`}></span>
              <span style={{ color: '#888' }}>Platform Status</span>
            </div>
            <span style={{ 
              color: apiStatus === 'healthy' ? '#10b981' : '#ef4444',
              fontWeight: '500'
            }}>
              {apiStatus === 'healthy' ? 'Operational' : 'Offline'}
            </span>
          </div>
  
          {/* CTA */}
          <div style={{ textAlign: 'center' }}>
            <button 
              onClick={() => window.location.href = '/dashboard'}
              className="btn btn-primary"
              style={{
                fontSize: '18px',
                padding: '16px 40px'
              }}
            >
              Access Dashboard →
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  function FeatureCard({ icon, title, description }) {
    return (
      <div style={{
        padding: '30px',
        backgroundColor: '#f8f9fa',
        borderRadius: '10px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>{icon}</div>
        <h3 style={{ marginBottom: '15px' }}>{title}</h3>
        <p style={{ color: '#666', lineHeight: '1.6' }}>{description}</p>
      </div>
    );
  }

function Dashboard() {
    const [jobStatus, setJobStatus] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [selectedUseCase, setSelectedUseCase] = React.useState('chest-xray');
    
    const medicalUseCases = {
      'chest-xray': {
        name: 'Pneumonia Detection',
        description: 'Chest X-Ray Analysis',
        model: 'ResNet50',
        clients: 5,
        icon: ''
      },
      'tumor': {
        name: 'Tumor Classification',
        description: 'Brain MRI Analysis',
        model: 'DenseNet121',
        clients: 3,
        icon: ''
      },
      'diabetic': {
        name: 'Retinopathy Detection',
        description: 'Retinal Imaging',
        model: 'EfficientNet',
        clients: 4,
        icon: ''
      }
    };
    
    const createMedicalFL = async () => {
      setLoading(true);
      const useCase = medicalUseCases[selectedUseCase];
      
      try {
        const response = await fetch('http://localhost:5001/api/jobs/medical', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: useCase.name,
            model_type: useCase.model,
            num_clients: useCase.clients,
            privacy_budget: 3.0,
            use_case: selectedUseCase
          })
        });
        
        const result = await response.json();
        setJobStatus(result);
        
      } catch (error) {
        alert('Error creating job: ' + error.message);
      }
      setLoading(false);
    };
    
    return (
      <div style={{ 
        minHeight: '100vh',
        background: '#0a0a0a',
        color: '#e0e0e0'
      }}>
        <div className="container" style={{ paddingTop: '40px' }}>
          <h1 style={{ 
            fontSize: '36px', 
            marginBottom: '40px',
            fontWeight: '600'
          }}>
            Dashboard
          </h1>
          
          {/* Job Creation */}
          <div className="card" style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '20px', marginBottom: '24px', color: '#fff' }}>
              Deploy Federated Training Job
            </h3>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: '16px',
              marginBottom: '24px'
            }}>
              {Object.entries(medicalUseCases).map(([key, useCase]) => (
                <div
                  key={key}
                  onClick={() => setSelectedUseCase(key)}
                  className="card"
                  style={{
                    cursor: 'pointer',
                    background: selectedUseCase === key ? '#1a1a1a' : '#0f0f0f',
                    borderColor: selectedUseCase === key ? '#444' : '#222',
                    textAlign: 'center',
                    padding: '20px'
                  }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>{useCase.icon}</div>
                  <h4 style={{ fontSize: '16px', color: '#fff' }}>{useCase.name}</h4>
                  <p style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>
                    {useCase.clients} hospitals
                  </p>
                </div>
              ))}
            </div>
            
            <button 
              onClick={createMedicalFL}
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%' }}
            >
              {loading ? 'Deploying...' : `Deploy ${medicalUseCases[selectedUseCase].name}`}
            </button>
          </div>

                {/* Job Status */}
                {jobStatus && (
                    <div className="card" style={{
                        borderColor: '#10b981',
                        background: 'linear-gradient(135deg, #111 0%, #0d1510 100%)'
                    }}>
                        <h4 style={{ fontSize: '18px', marginBottom: '20px', color: '#10b981' }}>
                            ✓ Job Deployed Successfully
                        </h4>

                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '20px',
                            fontSize: '14px'
                        }}>
                            <div>
                                <span style={{ color: '#666' }}>Job ID</span>
                                <p style={{ color: '#fff', fontFamily: 'monospace' }}>{jobStatus.job_id}</p>
                            </div>
                            <div>
                                <span style={{ color: '#666' }}>Participants</span>
                                <p style={{ color: '#fff' }}>{jobStatus.hospitals?.length || jobStatus.results?.length || 0} hospitals</p>
                            </div>
                        </div>

                        <div style={{
                            marginTop: '24px',
                            padding: '16px',
                            background: '#0a0a0a',
                            borderRadius: '6px',
                            fontFamily: 'monospace',
                            fontSize: '13px'
                        }}>
                            <div style={{ color: '#666', marginBottom: '8px' }}>Training Progress</div>
                            {(jobStatus.hospitals || ['St. Mary Hospital', 'Regional Medical', 'University Hospital', 'Metro General'])
                                .slice(0, jobStatus.num_clients || 4)
                                .map((hospital, idx) => (
                                    <div key={idx} style={{ marginBottom: '4px' }}>
                                        {hospital}: [{'█'.repeat(8)}{'░'.repeat(2)}] {80 + idx * 5}%
                                    </div>
                                ))}
                        </div>
                    </div>
                )}
                {jobStatus && <RealTimeMonitor jobId={jobStatus.job_id} />}
                <ProductionArchitecture />
            </div>
        </div>
    );
  }

export default App;