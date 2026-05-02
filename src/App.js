import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import DeviceCard from './components/DeviceCard';
import HistoryTable from './components/HistoryTable';
import StatusBar from './components/StatusBar';

function App() {
  const [devices, setDevices] = useState([]);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [countdown, setCountdown] = useState(5);
  const [executing, setExecuting] = useState(false);

  const API_URL = 'http://localhost:5000/api';

  // Función para obtener datos
  const fetchData = async () => {
    try {
      const [devicesRes, statusRes, historyRes] = await Promise.all([
        axios.get(`${API_URL}/devices`),
        axios.get(`${API_URL}/status`),
        axios.get(`${API_URL}/history`)
      ]);

      setDevices(devicesRes.data);
      setStatus(statusRes.data);
      setHistory(historyRes.data);
      setLoading(false);
      setCountdown(5);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  // Función para ejecutar main.py desde el frontend
  const handleRunMain = async () => {
    try {
      setExecuting(true);
      const response = await axios.post(`${API_URL}/run-main`);
      
      console.log('main.py ejecutado:', response.data);
      
      // Esperar un segundo y luego actualizar datos
      setTimeout(() => {
        fetchData();
        setExecuting(false);
      }, 2000);
    } catch (error) {
      console.error('Error ejecutando main.py:', error);
      setExecuting(false);
    }
  };

  // Obtener datos al montar el componente
  useEffect(() => {
    fetchData();
  }, []);

  // Actualizar cada 5 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Countdown para siguiente actualización
  useEffect(() => {
    const countdownInterval = setInterval(() => {
      setCountdown(prev => (prev <= 1 ? 5 : prev - 1));
    }, 1000);

    return () => clearInterval(countdownInterval);
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Monitor de Dispositivos Android</h1>
          <p>Sistema de Automatizacion en Tiempo Real - Be Digital</p>
          <button 
            className={`run-main-btn ${executing ? 'executing' : ''}`}
            onClick={handleRunMain}
            disabled={executing}
          >
            {executing ? 'Ejecutando...' : 'Ejecutar'}
          </button>
        </div>
      </header>

      {status && <StatusBar status={status} countdown={countdown} />}

      <main className="main-content">
        <div className="devices-section">
          <h2>Dispositivos Conectados</h2>
          <div className="devices-grid">
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Cargando datos...</p>
              </div>
            ) : devices.length === 0 ? (
              <div className="no-devices">
                <div className="icon">---</div>
                <p>Esperando que se conecte un dispositivo...</p>
                <p style={{ fontSize: '0.9em', marginTop: '10px', color: '#999' }}>
                  Presiona "Ejecutar main.py" para recolectar datos
                </p>
              </div>
            ) : (
              devices.map((device, index) => (
                <DeviceCard key={index} device={device} />
              ))
            )}
          </div>
        </div>

        <div className="history-section">
          <h2>Historico de Ejecuciones</h2>
          <HistoryTable history={history} />
        </div>
      </main>

      <footer className="footer">
        <p>Dashboard en Tiempo Real | Be Digital Automation System</p>
      </footer>
    </div>
  );
}

export default App;