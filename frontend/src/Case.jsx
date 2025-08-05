import React, { useState, useEffect } from 'react';
import './App.css';
import { createClient } from '@supabase/supabase-js';
import { Link } from 'react-router'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

const baseURL = 'https://api.disease-surveillance-dashboard.online';

const Case = () => {
  const [formData, setFormData] = useState({
    nik: '',
    Kode_kecamatan: '',
    ICD10_code: ''
  });

  const [statusMessage, setStatusMessage] = useState('');
  const [puskesmasOptions, setPuskesmasOptions] = useState([]);
  const [penyakitOptions, setPenyakitOptions] = useState([]);
  const [selectedPenyakitDescription, setSelectedPenyakitDescription] = useState('');

  // Fetch data from Supabase
  useEffect(() => {
    fetchPuskesmas();
    fetchPenyakit();
  }, []);

  const fetchPuskesmas = async () => {
    const { data, error } = await supabase.from('puskesmas').select('kode_kecamatan, nama_puskesmas');
    if (!error) {
      const formatted = data.map(p => ({
        value: p.kode_kecamatan,
        label: p.nama_puskesmas
      }));
      setPuskesmasOptions(formatted);
    } else {
      console.error('Error fetching puskesmas:', error.message);
    }
  };

  const fetchPenyakit = async () => {
    const { data, error } = await supabase.from('penyakit').select('icd10, nama_penyakit, keterangan');
    if (!error) {
      const formatted = data.map(p => ({
        value: p.icd10,
        label: `${p.nama_penyakit} (${p.icd10})`,
        description: p.keterangan
      }));
      setPenyakitOptions(formatted);
    } else {
      console.error('Error fetching penyakit:', error.message);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'icd10') {
      const selected = penyakitOptions.find(p => p.value === value);
      setSelectedPenyakitDescription(selected?.description || '');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(baseURL + '/submit_diagnosis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const result = await response.json();
      if (response.ok) {
        setStatusMessage(result.message);
      } else {
        throw new Error(result.detail);
      }
    } catch (error) {
      setStatusMessage(`Error: ${error.message}`);
    }
  };

  return (
    <div className="app">
        <nav>
        <Link to="/">
          <button>Lihat Dashboard</button>
        </Link>
      </nav>
      <header className="header">
        <h1>Submit Diagnosa</h1>
      </header>
      <div className="diagnosis-form-container">
        <form onSubmit={handleSubmit} className="diagnosis-form">
          <label htmlFor="nik">NIK Pasien:</label>
          <input
            type="text"
            name="nik"
            value={formData.nik}
            onChange={handleChange}
            required
          />

          <label htmlFor="Kode_kecamatan">Puskesmas:</label>
          <select
            name="Kode_kecamatan"
            value={formData.Kode_kecamatan}
            onChange={handleChange}
            required
          >
            <option value="">Pilih Puskesmas</option>
            {puskesmasOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <label htmlFor="icd10">Nama Penyakit:</label>
          <select
            name="icd10"
            value={formData.ICD10_code}
            onChange={handleChange}
            required
          >
            <option value="">Pilih Penyakit</option>
            {penyakitOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          {selectedPenyakitDescription && (
            <div className="penyakit-description">
              <label>Gejala Penyakit:</label>
              <textarea
                readOnly
                value={selectedPenyakitDescription}
                rows={4}
                style={{ width: '100%' }}
              />
            </div>
          )}

          <button type="submit">Submit</button>
        </form>
        {statusMessage && <p className="status-message">{statusMessage}</p>}
      </div>
    </div>
  );
};

export default Case;