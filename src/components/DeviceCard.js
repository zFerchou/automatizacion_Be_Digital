import React from 'react';

function DeviceCard({ device }) {
  // Verificar si el device existe y tiene datos
  if (!device || (!device.bateria && device.estado !== 'desconectado')) {
    return null;
  }

  const screenshots = device.screenshots || [];
  const lastScreenshot = screenshots.length > 0 ? screenshots[0] : null;
  const desconectado = device.estado === 'desconectado';

  return (
    <div className={`device-card${desconectado ? ' disconnected' : ''}`}>
      <div className="device-header">
        <span className="device-name">{device.id_dispositivo || 'Desconocido'}</span>
        <span className="device-status">
          {desconectado ? (
            <span style={{ color: '#f44336' }}></span>
          ) : (
            <span style={{ color: '#4caf50' }}></span>
          )}
        </span>
      </div>

      {!desconectado && (
        <>
          <div className="metric">
            <div className="metric-label">Batería</div>
            <div className="metric-value">{device.bateria?.porcentaje || 0}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${device.bateria?.porcentaje || 0}%` }}
              >
                {device.bateria?.porcentaje || 0}%
              </div>
            </div>
          </div>

          <div className="metric">
            <div className="metric-label">Almacenamiento Disponible</div>
            <div className="metric-value">
              {(device.almacenamiento?.porcentaje_libre || 0).toFixed(1)}%
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${Math.min(device.almacenamiento?.porcentaje_libre || 0, 100)}%` }}
              >
                {(device.almacenamiento?.porcentaje_libre || 0).toFixed(1)}%
              </div>
            </div>
            <div className="metric-details">
              <strong>Detalles:</strong>
              <br />
              Usado: {device.almacenamiento?.usado_mb || 0} MB | 
              Total: {device.almacenamiento?.total_mb || 0} MB
            </div>
          </div>

          <div className="metric">
            <div className="metric-label">Acciones Ejecutadas</div>
            <div>
              <span 
                className={`action-badge ${
                  device.acciones?.screenshot_tomado ? 'warning' : 'success'
                }`}
              >
                Screenshot: {device.acciones?.screenshot_tomado ? '✓ SÍ' : '✗ NO'}
              </span>
              {lastScreenshot && (
                <a 
                  href={`http://localhost:5000/api/screenshot/${lastScreenshot}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="screenshot-link"
                >
                  Ver Imagen
                </a>
              )}
              <br />
              <span className="action-badge success">
                App: {device.acciones?.app_abierta ? 'Abierta' : 'Cerrada'}
              </span>
            </div>
          </div>
        </>
      )}

      <div className="timestamp">
        {device.timestamp_legible || 'Sin datos'}
      </div>
      {desconectado && (
        <div className="disconnect-log">Dispositivo desconectado</div>
      )}
    </div>
  );
}

export default DeviceCard;