import React from 'react';

function LogViewer({ logs }) {
  // Protección completa contra undefined
  const safeLogs = logs || {};
  const logLines = Array.isArray(safeLogs.logs) ? safeLogs.logs : [];
  const errors = Array.isArray(safeLogs.errors) ? safeLogs.errors : [];
  const warnings = Array.isArray(safeLogs.warnings) ? safeLogs.warnings : [];
  const totalLines = safeLogs.total_lines || logLines.length;

  // Si no hay logs
  if (logLines.length === 0) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center', 
        color: '#666',
        background: '#1e1e1e',
        borderRadius: '8px',
        margin: '20px 0'
      }}>
        <p> Esperando logs de ejecución...</p>
        <p style={{ fontSize: '0.8em', marginTop: '10px' }}>
          Presiona "Ejecutar" para iniciar la automatización
        </p>
      </div>
    );
  }

  const getLogStyle = (log) => {
    if (log.includes('ERROR') || log.includes('❌')) {
      return { color: '#ff6b6b', fontWeight: 'bold' };
    }
    if (log.includes('WARNING') || log.includes('WARN') || log.includes('⚠️')) {
      return { color: '#ffd93d' };
    }
    if (log.includes('') || log.includes('COMPLETADA') || log.includes('EXITOSAMENTE')) {
      return { color: '#51cf66' };
    }
    if (log.includes('') || log.includes('INICIANDO') || log.includes('INFO')) {
      return { color: '#6bb5ff' };
    }
    return { color: '#ccc' };
  };

  return (
    <div style={{
      background: '#1e1e1e',
      borderRadius: '8px',
      padding: '15px',
      margin: '20px 0'
    }}>
      {/* Stats */}
      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        marginBottom: '12px',
        padding: '8px 12px',
        background: '#2a2a2a',
        borderRadius: '4px',
        fontSize: '0.85em',
        flexWrap: 'wrap'
      }}>
        <span style={{ color: '#aaa' }}>
           <strong>{totalLines}</strong> líneas
        </span>
        {errors.length > 0 && (
          <span style={{ color: '#ff6b6b' }}>
             <strong>{errors.length}</strong> errores
          </span>
        )}
        {warnings.length > 0 && (
          <span style={{ color: '#ffd93d' }}>
             <strong>{warnings.length}</strong> warnings
          </span>
        )}
      </div>

      {/* Log container */}
      <div style={{
        maxHeight: '400px',
        overflowY: 'auto',
        fontFamily: "'Courier New', monospace",
        fontSize: '0.82em',
        background: '#0d0d0d',
        padding: '10px',
        borderRadius: '4px',
        lineHeight: '1.6'
      }}>
        {logLines.map((log, index) => (
          <div 
            key={index} 
            style={{
              display: 'flex',
              padding: '1px 0',
              background: log.includes('ERROR') || log.includes('') ? 'rgba(255,0,0,0.1)' : 'transparent'
            }}
          >
            <span style={{ 
              color: '#555', 
              marginRight: '12px', 
              minWidth: '35px',
              textAlign: 'right',
              userSelect: 'none'
            }}>
              {index + 1}
            </span>
            <span style={{ 
              ...getLogStyle(log),
              wordBreak: 'break-all'
            }}>
              {log}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LogViewer;