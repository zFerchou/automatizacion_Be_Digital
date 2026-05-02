import React from 'react';

function HistoryTable({ history }) {
  // Filtrar items válidos
  const validHistory = (history || []).filter(item => item && item.id_dispositivo);

  return (
    <div className="history-table">
      <table>
        <thead>
          <tr>
            <th>Dispositivo</th>
            <th>Fecha/Hora</th>
            <th>Batería</th>
            <th>Almacenamiento</th>
            <th>Screenshot</th>
            <th>API</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {validHistory.length === 0 ? (
            <tr>
              <td colSpan="7" className="empty-state">
                <div className="spinner" style={{ margin: '0 auto', marginBottom: '10px' }}></div>
                <div>Esperando datos...</div>
              </td>
            </tr>
          ) : (
            validHistory.map((item, index) => {
              // Buscar screenshot más reciente si existe
              let screenshotUrl = null;
              if (item.screenshots && item.screenshots.length > 0) {
                screenshotUrl = `http://localhost:5000/api/screenshot/${item.screenshots[0]}`;
              }
              if (item.isDisconnectLog) {
                return (
                  <tr key={index} className="disconnected-row">
                    <td colSpan="7" style={{ textAlign: 'center', fontWeight: 'bold', color: '#f44336' }}>
                      {item.mensaje || 'Dispositivo desconectado'}
                    </td>
                  </tr>
                );
              }
              return (
                <tr key={index} className={item.estado === 'desconectado' ? 'disconnected-row' : ''}>
                  <td><strong>{item.id_dispositivo || 'Desconocido'}</strong></td>
                  <td>{item.timestamp_legible || item.timestamp_iso || 'Sin datos'}</td>
                  <td>
                    {item.bateria ? (
                      <span className="status-badge status-ok">
                        {item.bateria?.porcentaje || 0}%
                      </span>
                    ) : '--'}
                  </td>
                  <td>
                    {item.almacenamiento ? (
                      <span 
                        className={`status-badge ${
                          (item.almacenamiento?.porcentaje_libre || 0) < 10 
                            ? 'status-warning' 
                            : 'status-ok'
                        }`}
                      >
                        {(item.almacenamiento?.porcentaje_libre || 0).toFixed(1)}%
                      </span>
                    ) : '--'}
                  </td>
                  <td>
                    {screenshotUrl ? (
                      <a href={screenshotUrl} target="_blank" rel="noopener noreferrer" className="screenshot-link">Ver imagen</a>
                    ) : (
                      '--'
                    )}
                  </td>
                  <td>
                    <span className="status-badge status-ok">✓ OK</span>
                  </td>
                  <td>
                    {item.estado === 'desconectado' ? (
                      <span className="status-badge status-disconnected">Desconectado</span>
                    ) : (
                      <span className="status-badge status-ok">Conectado</span>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export default HistoryTable;