import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import DeviceCard from './components/DeviceCard';
import HistoryTable from './components/HistoryTable';
import StatusBar from './components/StatusBar';
import LogViewer from './components/LogViewer';

function App() {
  const [devices, setDevices] = useState([]);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState({ 
    logs: ['Cargando...'], 
    errors: [], 
    warnings: [], 
    total_lines: 1 
  });
  const [loading, setLoading] = useState(true);
  const [countdown, setCountdown] = useState(5);
  const [executing, setExecuting] = useState(false);

  const API_URL = 'http://localhost:5000/api';

  const fetchData = async () => {
    try {
      const [devicesRes, statusRes, historyRes, logsRes] = await Promise.all([
        axios.get(`${API_URL}/devices`),
        axios.get(`${API_URL}/status`),
        axios.get(`${API_URL}/history`),
        axios.get(`${API_URL}/logs`)
      ]);

      setDevices(Array.isArray(devicesRes.data) ? devicesRes.data : []);
      setStatus(statusRes.data || null);
      setHistory(Array.isArray(historyRes.data) ? historyRes.data : []);
      
      if (logsRes.data && logsRes.data.logs) {
        setLogs({
          logs: Array.isArray(logsRes.data.logs) ? logsRes.data.logs : [],
          errors: Array.isArray(logsRes.data.errors) ? logsRes.data.errors : [],
          warnings: Array.isArray(logsRes.data.warnings) ? logsRes.data.warnings : [],
          total_lines: logsRes.data.total_lines || 0
        });
      }
      
      setLoading(false);
      setCountdown(5);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const handleRunMain = async () => {
    try {
      setExecuting(true);
      await axios.post(`${API_URL}/run-main`);
      
      setTimeout(() => {
        fetchData();
        setExecuting(false);
      }, 3000);
    } catch (error) {
      console.error('Error ejecutando main.py:', error);
      alert('Error al ejecutar main.py');
      setExecuting(false);
      fetchData();
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

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
          <h2>Dispositivos Registrados</h2>
          <div className="devices-grid">
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Cargando datos...</p>
              </div>
            ) : devices.length === 0 ? (
              <div className="no-devices">
                <p>No hay dispositivos registrados</p>
                <p style={{ fontSize: '0.9em', marginTop: '10px', color: '#999' }}>
                  Conecte un dispositivo y presione "Ejecutar"
                </p>
              </div>
            ) : (
              devices.map((device, index) => (
                <DeviceCard key={index} device={device} />
              ))
            )}
          </div>
        </div>

        <div className="logs-section">
          <h2>Log de Ejecucion</h2>
          <LogViewer logs={logs} />
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