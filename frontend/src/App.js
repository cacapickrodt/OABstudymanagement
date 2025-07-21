import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [disciplinas, setDisciplinas] = useState([]);
  const [desempenhoSemanal, setDesempenhoSemanal] = useState(null);
  const [semanaAtual, setSemanaAtual] = useState(getCurrentWeekStart());
  const [loading, setLoading] = useState(false);
  
  // Get current week start date (Monday)
  function getCurrentWeekStart() {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is Sunday
    return new Date(today.setDate(diff)).toISOString().split('T')[0];
  }

  // Load disciplines on component mount
  useEffect(() => {
    loadDisciplinas();
    loadDesempenho();
  }, [semanaAtual]);

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
              {disciplinas.map((disciplina) => (
                <div key={disciplina.id} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-3">
                    {disciplina.nome}
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-4">
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
                </div>
              ))}
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
