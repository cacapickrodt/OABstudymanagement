import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [disciplinas, setDisciplinas] = useState([]);
  const [desempenhoSemanal, setDesempenhoSemanal] = useState(null);
  const [semanaAtual, setSemanaAtual] = useState(getCurrentWeekStart());
  const [loading, setLoading] = useState(false);
  const [timers, setTimers] = useState({}); // Track timer states
  const [resumoTempo, setResumoTempo] = useState([]); // Weekly time summary
  
  // Get current week start date (Monday)
  function getCurrentWeekStart() {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is Sunday
    return new Date(today.setDate(diff)).toISOString().split('T')[0];
  }

  // Format seconds to hours and minutes
  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Load disciplines on component mount
  useEffect(() => {
    loadDisciplinas();
    loadDesempenho();
    loadResumoTempo();
  }, [semanaAtual]);

  // Check timer status for all disciplines
  const checkTimerStatus = useCallback(async () => {
    if (disciplinas.length === 0) return;
    
    const timerPromises = disciplinas.map(async (disciplina) => {
      try {
        const response = await axios.get(`${API}/timer/status/${disciplina.id}`);
        return { disciplinaId: disciplina.id, status: response.data };
      } catch (error) {
        console.error(`Erro ao verificar timer da disciplina ${disciplina.id}:`, error);
        return { disciplinaId: disciplina.id, status: { ativo: false } };
      }
    });

    const results = await Promise.all(timerPromises);
    const newTimers = {};
    
    results.forEach(({ disciplinaId, status }) => {
      newTimers[disciplinaId] = {
        ativo: status.ativo,
        duracaoAtual: status.duracao_atual_segundos || 0,
        inicio: status.sessao?.inicio || null
      };
    });
    
    setTimers(newTimers);
  }, [disciplinas]);

  // Update timer display every second
  useEffect(() => {
    const interval = setInterval(() => {
      setTimers(prev => {
        const updated = { ...prev };
        Object.keys(updated).forEach(disciplinaId => {
          if (updated[disciplinaId].ativo && updated[disciplinaId].inicio) {
            const inicioTime = new Date(updated[disciplinaId].inicio);
            const now = new Date();
            updated[disciplinaId].duracaoAtual = Math.floor((now - inicioTime) / 1000);
          }
        });
        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    checkTimerStatus();
  }, [checkTimerStatus]);

  const loadDisciplinas = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/disciplinas`);
      setDisciplinas(response.data);
    } catch (error) {
      console.error('Erro ao carregar disciplinas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDesempenho = async () => {
    try {
      const response = await axios.get(`${API}/desempenho/${semanaAtual}`);
      setDesempenhoSemanal(response.data);
    } catch (error) {
      console.error('Erro ao carregar desempenho:', error);
    }
  };

  const loadResumoTempo = async () => {
    try {
      const response = await axios.get(`${API}/timer/resumo-semanal`);
      setResumoTempo(response.data);
    } catch (error) {
      console.error('Erro ao carregar resumo de tempo:', error);
    }
  };

  const updateDisciplinaHorario = async (disciplinaId, horarioInicio, horarioFim) => {
    try {
      await axios.put(`${API}/disciplinas/${disciplinaId}`, {
        horario_inicio: horarioInicio,
        horario_fim: horarioFim
      });
      // Update local state
      setDisciplinas(prev => prev.map(d => 
        d.id === disciplinaId 
          ? { ...d, horario_inicio: horarioInicio, horario_fim: horarioFim }
          : d
      ));
    } catch (error) {
      console.error('Erro ao atualizar horário:', error);
    }
  };

  const iniciarTimer = async (disciplinaId) => {
    try {
      const response = await axios.post(`${API}/timer/iniciar`, {
        disciplina_id: disciplinaId
      });
      
      // Update timer state
      setTimers(prev => ({
        ...prev,
        [disciplinaId]: {
          ativo: true,
          duracaoAtual: 0,
          inicio: response.data.inicio
        }
      }));
    } catch (error) {
      console.error('Erro ao iniciar timer:', error);
      alert('Erro ao iniciar cronômetro. Verifique se não há outro ativo para esta disciplina.');
    }
  };

  const pararTimer = async (disciplinaId) => {
    try {
      const response = await axios.put(`${API}/timer/parar/${disciplinaId}`);
      
      // Update timer state
      setTimers(prev => ({
        ...prev,
        [disciplinaId]: {
          ativo: false,
          duracaoAtual: 0,
          inicio: null
        }
      }));

      // Refresh weekly summary
      loadResumoTempo();
      
      alert(`Cronômetro parado! Tempo estudado: ${response.data.duracao_formatada}`);
    } catch (error) {
      console.error('Erro ao parar timer:', error);
      alert('Erro ao parar cronômetro.');
    }
  };

  const addTarefa = (dia) => {
    if (!desempenhoSemanal) return;
    
    const novaTarefa = {
      id: Date.now().toString(),
      horario: "09:00",
      descricao: "Nova tarefa",
      concluida: false
    };

    setDesempenhoSemanal(prev => ({
      ...prev,
      [dia]: [...(prev[dia] || []), novaTarefa]
    }));
  };

  const updateTarefa = (dia, tarefaId, field, value) => {
    setDesempenhoSemanal(prev => ({
      ...prev,
      [dia]: prev[dia].map(tarefa => 
        tarefa.id === tarefaId 
          ? { ...tarefa, [field]: value }
          : tarefa
      )
    }));
  };

  const diasSemana = [
    { key: 'segunda', label: 'Segunda' },
    { key: 'terca', label: 'Terça' },
    { key: 'quarta', label: 'Quarta' },
    { key: 'quinta', label: 'Quinta' },
    { key: 'sexta', label: 'Sexta' },
    { key: 'sabado', label: 'Sábado' },
    { key: 'domingo', label: 'Domingo' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-900 text-white py-6">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold text-center">
            PLANEJAMENTO DE ESTUDOS
          </h1>
          <p className="text-center text-blue-200 mt-2">
            Sistema de Organização para Estudos de Direito
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Coluna Disciplinas */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">DISCIPLINAS</h2>
              <button
                onClick={loadDisciplinas}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Carregando...' : 'Atualizar Disciplinas'}
              </button>
            </div>
            
            <div className="space-y-4">
              {disciplinas.map((disciplina) => {
                const timer = timers[disciplina.id] || { ativo: false, duracaoAtual: 0 };
                
                return (
                  <div key={disciplina.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-800 mb-3">
                      {disciplina.nome}
                    </h3>
                    
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Horário Início
                        </label>
                        <input
                          type="time"
                          value={disciplina.horario_inicio || ""}
                          onChange={(e) => updateDisciplinaHorario(
                            disciplina.id,
                            e.target.value,
                            disciplina.horario_fim
                          )}
                          className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Horário Fim
                        </label>
                        <input
                          type="time"
                          value={disciplina.horario_fim || ""}
                          onChange={(e) => updateDisciplinaHorario(
                            disciplina.id,
                            disciplina.horario_inicio,
                            e.target.value
                          )}
                          className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    {/* Cronometer Section */}
                    <div className="border-t pt-4 mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Cronômetro:</span>
                        <span className={`text-lg font-mono ${timer.ativo ? 'text-green-600' : 'text-gray-400'}`}>
                          {formatTime(timer.duracaoAtual)}
                        </span>
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => iniciarTimer(disciplina.id)}
                          disabled={timer.ativo}
                          className={`flex-1 py-2 px-4 rounded text-white font-medium ${
                            timer.ativo 
                              ? 'bg-gray-400 cursor-not-allowed' 
                              : 'bg-green-600 hover:bg-green-700'
                          }`}
                        >
                          {timer.ativo ? 'Em andamento' : 'Iniciar'}
                        </button>
                        
                        <button
                          onClick={() => pararTimer(disciplina.id)}
                          disabled={!timer.ativo}
                          className={`flex-1 py-2 px-4 rounded text-white font-medium ${
                            !timer.ativo 
                              ? 'bg-gray-400 cursor-not-allowed' 
                              : 'bg-red-600 hover:bg-red-700'
                          }`}
                        >
                          Parar
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Coluna Desempenho Semanal */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">DESEMPENHO SEMANAL</h2>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={semanaAtual}
                  onChange={(e) => setSemanaAtual(e.target.value)}
                  className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={loadDesempenho}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                  Carregar Desempenho
                </button>
              </div>
            </div>

            {/* Weekly Time Summary */}
            {resumoTempo.length > 0 && (
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-bold text-blue-800 mb-3">Resumo Semanal - Tempo de Estudo</h3>
                <div className="space-y-2">
                  {resumoTempo.map((item) => (
                    <div key={item.disciplina_id} className="flex justify-between items-center text-sm">
                      <span className="text-gray-700">{item.nome_disciplina}:</span>
                      <span className="font-mono text-blue-600">{formatTime(item.total_segundos)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-6">
              {diasSemana.map(({ key, label }) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-semibold text-gray-800">{label}</h3>
                    <button
                      onClick={() => addTarefa(key)}
                      className="bg-blue-500 text-white w-8 h-8 rounded-full hover:bg-blue-600"
                    >
                      +
                    </button>
                  </div>

                  <div className="space-y-2">
                    {desempenhoSemanal && desempenhoSemanal[key] && desempenhoSemanal[key].map((tarefa) => (
                      <div key={tarefa.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                        <input
                          type="checkbox"
                          checked={tarefa.concluida}
                          onChange={(e) => updateTarefa(key, tarefa.id, 'concluida', e.target.checked)}
                          className="w-5 h-5 text-blue-600"
                        />
                        
                        <input
                          type="time"
                          value={tarefa.horario}
                          onChange={(e) => updateTarefa(key, tarefa.id, 'horario', e.target.value)}
                          className="border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                        
                        <input
                          type="text"
                          value={tarefa.descricao}
                          onChange={(e) => updateTarefa(key, tarefa.id, 'descricao', e.target.value)}
                          className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
                          placeholder="Descrição da tarefa"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
