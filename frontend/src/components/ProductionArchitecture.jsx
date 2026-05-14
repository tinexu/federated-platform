// frontend/src/components/ProductionArchitecture.jsx
import React, { useState } from 'react';

function ProductionArchitecture() {
  const [activeTab, setActiveTab] = useState('overview');
  
  return (
    <div className="card" style={{ marginTop: '40px' }}>
      <h2 style={{ fontSize: '24px', marginBottom: '32px', color: '#fff' }}>
        Production Architecture
      </h2>
      
      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '8px',
        marginBottom: '32px',
        borderBottom: '1px solid #222',
        paddingBottom: '16px'
      }}>
        {['overview', 'integration', 'security'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="btn btn-secondary"
            style={{
              background: activeTab === tab ? '#1a1a1a' : 'transparent',
              borderColor: activeTab === tab ? '#444' : '#222',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div>
          <h3 style={{ fontSize: '18px', marginBottom: '20px', color: '#fff' }}>
            How Real Hospitals Connect
          </h3>
          
          <div style={{ 
            background: '#0f0f0f',
            border: '1px solid #222',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '24px'
          }}>
            <div style={{ fontFamily: 'monospace', fontSize: '14px', lineHeight: '2' }}>
              <div style={{ color: '#888' }}>// Hospital Infrastructure</div>
              <div>
                <span style={{ color: '#666' }}>PACS System</span> → 
                <span style={{ color: '#10b981' }}> MedFL Edge Server</span> → 
                <span style={{ color: '#3b82f6' }}> AWS Cloud</span>
              </div>
              <div style={{ color: '#666', marginTop: '12px' }}>
                ↑ Patient data stays here&nbsp;&nbsp;&nbsp;&nbsp;↑ Only models travel
              </div>
            </div>
          </div>

          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '16px' 
          }}>
            <div style={{ 
              background: '#0f0f0f',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '20px'
            }}>
              <h4 style={{ color: '#10b981', marginBottom: '12px' }}>On-Premise</h4>
              <ul style={{ fontSize: '14px', color: '#888', listStyle: 'none', lineHeight: '1.8' }}>
                <li>• DICOM Server</li>
                <li>• Edge Computing Node</li>
                <li>• Local GPU Training</li>
                <li>• PHI Never Leaves</li>
              </ul>
            </div>
            
            <div style={{ 
              background: '#0f0f0f',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '20px'
            }}>
              <h4 style={{ color: '#3b82f6', marginBottom: '12px' }}>Cloud Platform</h4>
              <ul style={{ fontSize: '14px', color: '#888', listStyle: 'none', lineHeight: '1.8' }}>
                <li>• Model Aggregation</li>
                <li>• Privacy Controls</li>
                <li>• Job Orchestration</li>
                <li>• Compliance Logging</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Integration Tab */}
      {activeTab === 'integration' && (
        <div>
          <h3 style={{ fontSize: '18px', marginBottom: '20px', color: '#fff' }}>
            Integration Steps
          </h3>
          
          <div style={{ 
            background: '#0f0f0f',
            border: '1px solid #222',
            borderRadius: '8px',
            padding: '24px',
            fontFamily: 'monospace',
            fontSize: '13px',
            overflow: 'auto'
          }}>
            <div style={{ color: '#888', marginBottom: '16px' }}># Install MedFL Edge Client</div>
            <div style={{ marginBottom: '16px' }}>
              <span style={{ color: '#3b82f6' }}>docker</span> run -d \<br/>
              &nbsp;&nbsp;--name medfl-client \<br/>
              &nbsp;&nbsp;-e <span style={{ color: '#10b981' }}>HOSPITAL_ID</span>=stjohns-medical \<br/>
              &nbsp;&nbsp;-e <span style={{ color: '#10b981' }}>PACS_SERVER</span>=192.168.1.100:104 \<br/>
              &nbsp;&nbsp;-e <span style={{ color: '#10b981' }}>API_KEY</span>=sk_prod_xxxxx \<br/>
              &nbsp;&nbsp;medfl/edge-client:latest
            </div>
            
            <div style={{ color: '#888', marginTop: '24px', marginBottom: '16px' }}>
              # Configure DICOM Integration
            </div>
            <div>
              medfl-cli configure dicom \<br/>
              &nbsp;&nbsp;--ae-title MEDFL_CLIENT \<br/>
              &nbsp;&nbsp;--modalities CT,MR,XR \<br/>
              &nbsp;&nbsp;--auto-anonymize
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div>
          <h3 style={{ fontSize: '18px', marginBottom: '20px', color: '#fff' }}>
            Security & Compliance
          </h3>
          
          <div style={{ 
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            {[
              { label: 'HIPAA BAA', status: true },
              { label: 'SOC 2 Type II', status: true },
              { label: 'End-to-End Encryption', status: true },
              { label: 'Zero-Trust Network', status: true },
              { label: 'Audit Logging', status: true },
              { label: 'FDA 510(k) Ready', status: false }
            ].map((item, idx) => (
              <div 
                key={idx}
                style={{ 
                  background: '#0f0f0f',
                  border: '1px solid #222',
                  borderRadius: '6px',
                  padding: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <span style={{ fontSize: '14px' }}>{item.label}</span>
                <span className={`status-indicator ${item.status ? 'status-healthy' : 'status-warning'}`}></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProductionArchitecture;