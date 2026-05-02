import React from 'react';

function StatusBar({ status, countdown }) {
  return (
    <div className="status-bar">
      <div className="status-item">
        <div className="spinner"></div>
        <div className="label">Estado:</div>
        <div className="value">Monitoriendo</div>
      </div>
      <div className="status-item">
        <div className="label">Dispositivos Conectados:</div>
        <div className="value">{status.dispositivos_conectados}</div>
      </div>
      <div className="status-item">
        <div className="label">Próxima Actualización:</div>
        <div className="value">{countdown}s</div>
      </div>
      <div className="status-item">
        <div className="label">Total Ejecuciones:</div>
        <div className="value">{status.total_ejecuciones}</div>
      </div>
    </div>
  );
}

export default StatusBar;
