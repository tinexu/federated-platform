import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import io from 'socket.io-client';

function RealTimeMonitor({ jobId }) {
  const [socket, setSocket] = useState(null);
  const [trainingData, setTrainingData] = useState([]);
  const [hospitalStatus, setHospitalStatus] = useState({});
  const [privacySpent, setPrivacySpent] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  
  useEffect(() => {
    // Connect to WebSocket
    const newSocket = io('http://localhost:5001');
    setSocket(newSocket);
    
    // Start monitoring this job
    newSocket.emit('start_monitoring', { job_id: jobId });
    
    // Listen for updates
    newSocket.on('training_update', (data) => {
      if (data.job_id === jobId) {
        const metrics = data.metrics;
        
        // Format data for chart
        const chartPoint = {
          round: metrics.round,
          'Global Model': (metrics.global_accuracy * 100).toFixed(1),
          ...Object.entries(metrics.hospital_accuracy).reduce((acc, [hospital, accuracy]) => {
            acc[hospital] = (accuracy * 100).toFixed(1);
            return acc;
          }, {})
        };
        
        setTrainingData(prev => [...prev, chartPoint]);
        setHospitalStatus(metrics.hospital_status);
        setPrivacySpent(metrics.privacy_spent);
      }
    });
    
    newSocket.on('training_complete', (data) => {
      if (data.job_id === jobId) {
        setIsComplete(true);
      }
    });
    
    return () => {
      newSocket.close();
    };
  }, [jobId]);
  
  return (
    <div className="card" style={{ marginTop: '32px' }}>
      <h3 style={{ fontSize: '20px', marginBottom: '24px', color: '#fff' }}>
        Live Training Progress
      </h3>
      
      {/* Accuracy Chart */}
      <div style={{ marginBottom: '32px' }}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trainingData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="round" 
              stroke="#666"
              label={{ value: 'Training Round', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              stroke="#666"
              label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              contentStyle={{ 
                background: '#1a1a1a', 
                border: '1px solid #333',
                borderRadius: '6px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="Global Model" 
              stroke="#10b981" 
              strokeWidth={3}
              dot={{ fill: '#10b981', r: 4 }}
            />
            {Object.keys(hospitalStatus).map((hospital, idx) => (
              <Line
                key={hospital}
                type="monotone"
                dataKey={hospital}
                stroke={`hsl(${200 + idx * 30}, 70%, 50%)`}
                strokeWidth={1}
                strokeDasharray={hospitalStatus[hospital] === 'waiting' ? '5 5' : '0'}
                opacity={hospitalStatus[hospital] === 'waiting' ? 0.3 : 1}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Hospital Status Grid */}
      <div style={{ marginBottom: '24px' }}>
        <h4 style={{ fontSize: '16px', marginBottom: '16px', color: '#888' }}>
          Hospital Network Status
        </h4>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px'
        }}>
          {Object.entries(hospitalStatus).map(([hospital, status]) => (
            <div 
              key={hospital}
              style={{
                background: '#0f0f0f',
                border: '1px solid #222',
                borderRadius: '6px',
                padding: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <span style={{ fontSize: '13px', color: '#fff' }}>{hospital}</span>
              <span 
                style={{ 
                  fontSize: '12px',
                  color: status === 'complete' ? '#10b981' : 
                         status === 'training' ? '#3b82f6' : '#666',
                  textTransform: 'uppercase'
                }}
              >
                {status}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Privacy Budget */}
      <div style={{ marginBottom: '24px' }}>
        <h4 style={{ fontSize: '16px', marginBottom: '12px', color: '#888' }}>
          Privacy Budget Consumption
        </h4>
        <div style={{ 
          background: '#0f0f0f',
          border: '1px solid #222',
          borderRadius: '6px',
          padding: '16px'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            marginBottom: '8px'
          }}>
            <span style={{ fontSize: '14px' }}>Used: {privacySpent.toFixed(1)}</span>
            <span style={{ fontSize: '14px' }}>Limit: 3.0</span>
          </div>
          <div style={{ 
            background: '#1a1a1a',
            height: '8px',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div 
              style={{
                background: privacySpent > 2.5 ? '#f59e0b' : '#10b981',
                height: '100%',
                width: `${(privacySpent / 3.0) * 100}%`,
                transition: 'width 0.5s ease'
              }}
            />
          </div>
        </div>
      </div>
      
      {/* Completion Status */}
      {isComplete && (
        <div style={{ 
          background: 'linear-gradient(135deg, #0f0f0f 0%, #0d1510 100%)',
          border: '1px solid #10b981',
          borderRadius: '6px',
          padding: '20px',
          textAlign: 'center'
        }}>
          <h4 style={{ color: '#10b981', marginBottom: '8px' }}>
            Training Complete!
          </h4>
          <p style={{ color: '#888', fontSize: '14px' }}>
            Global model achieved superior performance through federated learning
          </p>
        </div>
      )}
    </div>
  );
}

export default RealTimeMonitor;