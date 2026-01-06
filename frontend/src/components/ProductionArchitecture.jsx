import React, { useState } from 'react';

function ProductionArchitecture() {
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <div style={{ 
      marginTop: '40px', 
      padding: '30px', 
      backgroundColor: '#f8f9fa', 
      borderRadius: '10px' 
    }}>
      <h2>🏗️ Production Architecture</h2>
      <p>How real hospitals connect to MedFL Platform:</p>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr', 
        gap: '20px',
        marginTop: '20px' 
      }}>
        {/* Hospital Side */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          border: '2px solid #e9ecef'
        }}>
          <h3>Hospital Infrastructure</h3>
          
          <div style={{ marginTop: '15px' }}>
            <h4>1. PACS Integration</h4>
            <code style={{ 
              backgroundColor: '#f4f4f4', 
              padding: '10px', 
              borderRadius: '4px',
              display: 'block',
              fontSize: '12px'
            }}>
              # MedFL DICOM Connector<br/>
              medfl-client connect \<br/>
              &nbsp;&nbsp;--pacs-server hospital-pacs.local:104 \<br/>
              &nbsp;&nbsp;--modality CT,MR,XR \<br/>
              &nbsp;&nbsp;--study-filter "pneumonia|covid|lung"
            </code>
          </div>
          
          <div style={{ marginTop: '15px' }}>
            <h4>2. On-Premise Edge Server</h4>
            <ul style={{ fontSize: '14px', lineHeight: '1.8' }}>
              <li>Docker container running in hospital DMZ</li>
              <li>Connects to PACS via DICOM protocol</li>
              <li>Pre-processes images (de-identification)</li>
              <li>Caches data locally (no cloud storage)</li>
            </ul>
          </div>
          
          <div style={{ marginTop: '15px' }}>
            <h4>3. Security Requirements</h4>
            <div style={{ 
              backgroundColor: '#e7f3ff', 
              padding: '15px', 
              borderRadius: '4px',
              fontSize: '14px' 
            }}>
              ✓ Runs inside hospital firewall<br/>
              ✓ No PHI leaves premises<br/>
              ✓ TLS 1.3 for model updates<br/>
              ✓ Audit logs for compliance<br/>
              ✓ Role-based access (RBAC)
            </div>
          </div>
        </div>
        
        {/* Data Flow Diagram */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          border: '2px solid #e9ecef'
        }}>
          <h3>Data Flow (No Patient Data Leaves Hospital)</h3>
          
          <div style={{ 
            fontFamily: 'monospace', 
            fontSize: '14px',
            lineHeight: '1.6',
            marginTop: '15px'
          }}>
            <div>📊 PACS System (DICOM Images)</div>
            <div>&nbsp;&nbsp;&nbsp;↓</div>
            <div>🖥️ MedFL Edge Server (Hospital)</div>
            <div>&nbsp;&nbsp;&nbsp;├─ Load & preprocess images</div>
            <div>&nbsp;&nbsp;&nbsp;├─ Train local model</div>
            <div>&nbsp;&nbsp;&nbsp;└─ Extract model weights only</div>
            <div>&nbsp;&nbsp;&nbsp;↓</div>
            <div>🔐 Encrypted Model Updates (NOT data)</div>
            <div>&nbsp;&nbsp;&nbsp;↓</div>
            <div>☁️ MedFL Cloud Platform</div>
            <div>&nbsp;&nbsp;&nbsp;├─ Aggregate model updates</div>
            <div>&nbsp;&nbsp;&nbsp;├─ Apply differential privacy</div>
            <div>&nbsp;&nbsp;&nbsp;└─ Distribute improved model</div>
            <div>&nbsp;&nbsp;&nbsp;↓</div>
            <div>🏥 All Hospitals Get Better Model</div>
          </div>
        </div>
        
        {/* Integration Steps */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          border: '2px solid #e9ecef'
        }}>
          <h3>Hospital Onboarding Process</h3>
          
          <ol style={{ lineHeight: '2', fontSize: '14px' }}>
            <li>
              <strong>Security Review</strong>
              <ul>
                <li>HIPAA compliance attestation</li>
                <li>Network security assessment</li>
                <li>BAA (Business Associate Agreement)</li>
              </ul>
            </li>
            
            <li>
              <strong>Technical Setup (2-3 days)</strong>
              <ul>
                <li>Deploy MedFL Edge Server in DMZ</li>
                <li>Configure PACS connection</li>
                <li>Set up VPN tunnel to MedFL Cloud</li>
                <li>Test with synthetic data</li>
              </ul>
            </li>
            
            <li>
              <strong>Pilot Phase (2 weeks)</strong>
              <ul>
                <li>Run on historical data</li>
                <li>Validate model improvements</li>
                <li>Train radiology team</li>
              </ul>
            </li>
            
            <li>
              <strong>Production (Ongoing)</strong>
              <ul>
                <li>Automated nightly training</li>
                <li>Monthly model updates</li>
                <li>Quarterly compliance audits</li>
              </ul>
            </li>
          </ol>
        </div>
      </div>
      
      <button
        onClick={() => setShowDetails(!showDetails)}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          backgroundColor: '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        {showDetails ? 'Hide' : 'Show'} Technical Implementation Details
      </button>
      
      {showDetails && (
        <div style={{ 
          marginTop: '20px', 
          padding: '20px', 
          backgroundColor: '#f1f3f5',
          borderRadius: '5px' 
        }}>
          <h4>DICOM Integration Example</h4>
          <pre style={{ 
            backgroundColor: '#282c34', 
            color: '#abb2bf',
            padding: '15px',
            borderRadius: '4px',
            overflow: 'auto'
          }}>
{`# MedFL Client Configuration (hospital-config.yaml)
dicom:
  ae_title: "MEDFL_CLIENT"
  pacs_server: "192.168.1.100"
  pacs_port: 104
  pacs_ae_title: "HOSPITAL_PACS"
  
preprocessing:
  anonymization:
    remove_phi: true
    hash_patient_id: true
    remove_dates: true
  
  normalization:
    resize_to: [512, 512]
    bit_depth: 16
    window_center: 40
    window_width: 400
    
federated_learning:
  model: "densenet121"
  batch_size: 16
  local_epochs: 5
  differential_privacy:
    epsilon: 3.0  # HIPAA compliant
    delta: 1e-5
    
api:
  medfl_endpoint: "https://api.medfl.io/v1"
  api_key: "$" + "{MEDFL_API_KEY}"
  use_vpn: true`}
          </pre>
        </div>
      )}
    </div>
  );
}

export default ProductionArchitecture;