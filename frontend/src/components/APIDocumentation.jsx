// frontend/src/components/APIDocumentation.jsx
function APIDocumentation() {
    return (
      <div style={{ marginTop: '40px' }}>
        <h3>🔌 Hospital Integration API</h3>
        
        <div style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '20px', 
          borderRadius: '8px',
          fontFamily: 'monospace',
          fontSize: '14px'
        }}>
          <div style={{ marginBottom: '20px' }}>
            <strong>POST /api/v1/hospitals/register</strong><br/>
            Register new hospital in the network
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <strong>POST /api/v1/training/join</strong><br/>
            Join active federated learning round
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <strong>PUT /api/v1/models/upload</strong><br/>
            Upload encrypted model updates
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <strong>GET /api/v1/models/global</strong><br/>
            Download latest aggregated model
          </div>
        </div>
      </div>
    );
  }