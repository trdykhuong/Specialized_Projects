import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Plus, Search, Filter, 
         Trash2, Edit, ExternalLink, Calendar, Briefcase, TrendingUp, 
         Shield, Bell, Users, DollarSign, MapPin, Mail, Phone, 
         BarChart3, PieChart, List, Grid, Eye, MessageSquare, Star, RefreshCw } from 'lucide-react';

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL = 'http://localhost:5000';

const api = {
  analyzeJob: async (jobData) => {
    const response = await fetch(`${API_BASE_URL}/api/analyze-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData)
    });
    return response.json();
  },
  
  batchAnalyze: async (jobs) => {
    const response = await fetch(`${API_BASE_URL}/api/batch-analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobs })
    });
    return response.json();
  },
  
  checkBlacklist: async (job, blacklist) => {
    const response = await fetch(`${API_BASE_URL}/api/check-blacklist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job, blacklist })
    });
    return response.json();
  },
  
  getStats: async (jobs) => {
    const response = await fetch(`${API_BASE_URL}/api/stats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobs })
    });
    return response.json();
  },
  
  getModelInfo: async () => {
    const response = await fetch(`${API_BASE_URL}/api/model-info`);
    return response.json();
  },
  
  healthCheck: async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
};

// ============================================================================
// CONSTANTS
// ============================================================================

const RISK_LEVELS = {
  LOW: { label: 'Tin cậy', color: 'green', icon: CheckCircle, range: [0, 30] },
  MEDIUM: { label: 'Cần kiểm tra', color: 'yellow', icon: AlertTriangle, range: [31, 60] },
  HIGH: { label: 'Nguy cơ cao', color: 'red', icon: AlertCircle, range: [61, 100] }
};

const STATUS_OPTIONS = [
  { value: 'considering', label: 'Đang cân nhắc', color: 'blue' },
  { value: 'applied', label: 'Đã apply', color: 'purple' },
  { value: 'interview', label: 'Phỏng vấn', color: 'orange' },
  { value: 'offer', label: 'Nhận offer', color: 'green' },
  { value: 'rejected', label: 'Từ chối', color: 'gray' },
  { value: 'skipped', label: 'Bỏ qua', color: 'gray' }
];

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

export default function PersonalJobTracker() {
  const [jobs, setJobs] = useState([]);
  const [blacklist, setBlacklist] = useState({ emails: [], companies: [], phones: [] });
  const [view, setView] = useState('list');
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showBlacklistModal, setShowBlacklistModal] = useState(false);
  const [apiStatus, setApiStatus] = useState({ connected: false, mlAvailable: false });
  const [analyzing, setAnalyzing] = useState(false);

  // Check API connection on mount
  useEffect(() => {
    checkApiConnection();
    loadData();
  }, []);

  const checkApiConnection = async () => {
    try {
      const health = await api.healthCheck();
      const modelInfo = await api.getModelInfo();
      
      setApiStatus({
        connected: health.status === 'healthy',
        mlAvailable: health.ml_model_loaded || false,
        modelType: modelInfo.info?.model_type || 'Unknown'
      });
    } catch (error) {
      console.error('API connection failed:', error);
      setApiStatus({ connected: false, mlAvailable: false });
    }
  };

  const loadData = async () => {
    try {
      const jobsData = await window.storage.get('jobs-list');
      const blacklistData = await window.storage.get('blacklist-data');
      
      if (jobsData) setJobs(JSON.parse(jobsData.value));
      if (blacklistData) setBlacklist(JSON.parse(blacklistData.value));
    } catch (error) {
      setJobs([]);
      setBlacklist({ emails: [], companies: [], phones: [] });
    }
  };

  const saveJobs = async (updatedJobs) => {
    setJobs(updatedJobs);
    await window.storage.set('jobs-list', JSON.stringify(updatedJobs));
  };

  const saveBlacklist = async (updatedBlacklist) => {
    setBlacklist(updatedBlacklist);
    await window.storage.set('blacklist-data', JSON.stringify(updatedBlacklist));
  };

  // Analyze job with backend API
  const analyzeJobWithAPI = async (jobData) => {
    setAnalyzing(true);
    try {
      // First check blacklist
      const blacklistCheck = await api.checkBlacklist(jobData, blacklist);
      
      // Then analyze with ML/heuristic
      const analysis = await api.analyzeJob(jobData);
      
      if (analysis.success) {
        const result = analysis.data;
        
        // Merge blacklist warnings
        const allReasons = [...result.reasons];
        if (blacklistCheck.success && blacklistCheck.matches.has_match) {
          allReasons.unshift(...blacklistCheck.matches.details);
        }
        
        return {
          riskScore: result.risk_score,
          riskLevel: result.risk_level,
          riskReasons: allReasons,
          confidence: result.confidence,
          mlPrediction: result.ml_available,
          analysis: result.analysis
        };
      }
    } catch (error) {
      console.error('API analysis failed:', error);
      // Fallback to local heuristic
      return calculateLocalRiskScore(jobData);
    } finally {
      setAnalyzing(false);
    }
  };

  // Fallback local risk calculation
  const calculateLocalRiskScore = (job) => {
    let score = 0;
    const reasons = [];

    const description = (job.description + ' ' + job.title).toLowerCase();
    
    // Scam keywords
    const scamKeywords = ['đóng phí', 'việc nhẹ lương cao', 'kiếm tiền nhanh', 'mlm'];
    scamKeywords.forEach(kw => {
      if (description.includes(kw)) {
        score += 15;
        reasons.push(`Có từ khóa nghi ngờ: "${kw}"`);
      }
    });

    // Email check
    if (job.email?.includes('@gmail.com') || job.email?.includes('@yahoo.com')) {
      score += 10;
      reasons.push('Email cá nhân');
    }

    // Missing info
    if (!job.address || job.address.length < 10) {
      score += 15;
      reasons.push('Thiếu địa chỉ công ty');
    }

    return { 
      riskScore: Math.min(score, 100), 
      riskReasons: reasons,
      riskLevel: score <= 30 ? 'LOW' : score <= 60 ? 'MEDIUM' : 'HIGH',
      mlPrediction: false
    };
  };

  const getRiskLevel = (score) => {
    if (score <= 30) return 'LOW';
    if (score <= 60) return 'MEDIUM';
    return 'HIGH';
  };

  // Filter jobs
  const filteredJobs = jobs.filter(job => {
    const matchesSearch = searchTerm === '' || 
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.companyName?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filter === 'all') return matchesSearch;
    if (filter === 'high-risk') return matchesSearch && getRiskLevel(job.riskScore) === 'HIGH';
    if (filter === 'safe') return matchesSearch && getRiskLevel(job.riskScore) === 'LOW';
    return matchesSearch && job.status === filter;
  });

  // Stats
  const stats = {
    total: jobs.length,
    highRisk: jobs.filter(j => getRiskLevel(j.riskScore) === 'HIGH').length,
    applied: jobs.filter(j => j.status === 'applied').length,
    interview: jobs.filter(j => j.status === 'interview').length,
    offers: jobs.filter(j => j.status === 'offer').length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b-2 border-blue-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Job Tracker & Scam Analyzer</h1>
                <p className="text-sm text-gray-600">Quản lý tin tuyển dụng cá nhân thông minh</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* API Status Indicator */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-lg">
                <div className={`w-2 h-2 rounded-full ${apiStatus.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-xs text-gray-600">
                  {apiStatus.connected ? (
                    apiStatus.mlAvailable ? '🤖 ML Model Active' : '📊 Heuristic Mode'
                  ) : '⚠️ API Offline'}
                </span>
              </div>
              
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
              >
                <Plus className="w-5 h-5" />
                <span>Thêm tin mới</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-5 gap-4 mb-8">
          <StatCard icon={Briefcase} label="Tổng số tin" value={stats.total} color="blue" />
          <StatCard icon={AlertCircle} label="Nguy cơ cao" value={stats.highRisk} color="red" />
          <StatCard icon={Users} label="Đã apply" value={stats.applied} color="purple" />
          <StatCard icon={Calendar} label="Phỏng vấn" value={stats.interview} color="orange" />
          <StatCard icon={CheckCircle} label="Nhận offer" value={stats.offers} color="green" />
        </div>

        {/* Toolbar */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Tìm kiếm theo tên công ty, vị trí..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả</option>
                <option value="high-risk">Nguy cơ cao</option>
                <option value="safe">An toàn</option>
                <option value="considering">Đang cân nhắc</option>
                <option value="applied">Đã apply</option>
                <option value="interview">Phỏng vấn</option>
                <option value="offer">Nhận offer</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setView('list')}
                className={`p-2 rounded ${view === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <List className="w-5 h-5" />
              </button>
              <button
                onClick={() => setView('grid')}
                className={`p-2 rounded ${view === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setView('stats')}
                className={`p-2 rounded ${view === 'stats' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <BarChart3 className="w-5 h-5" />
              </button>

              <button
                onClick={() => setShowBlacklistModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Shield className="w-5 h-5" />
                <span>Blacklist</span>
              </button>
            </div>
          </div>
        </div>

        {/* Loading indicator */}
        {analyzing && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center space-x-3">
            <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
            <span className="text-blue-800">Đang phân tích với AI model...</span>
          </div>
        )}

        {/* Content */}
        {view === 'stats' ? (
          <StatsView jobs={jobs} />
        ) : view === 'grid' ? (
          <GridView jobs={filteredJobs} onSelect={setSelectedJob} onDelete={(id) => saveJobs(jobs.filter(j => j.id !== id))} />
        ) : (
          <ListView jobs={filteredJobs} onSelect={setSelectedJob} onDelete={(id) => saveJobs(jobs.filter(j => j.id !== id))} />
        )}

        {filteredJobs.length === 0 && (
          <div className="text-center py-16">
            <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Chưa có tin tuyển dụng nào</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
            >
              Thêm tin đầu tiên →
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddModal && (
        <AddJobModal
          onClose={() => setShowAddModal(false)}
          onSave={async (job) => {
            const analysis = await analyzeJobWithAPI(job);
            const newJob = { 
              ...job, 
              id: Date.now(), 
              ...analysis,
              createdAt: new Date().toISOString() 
            };
            saveJobs([...jobs, newJob]);
            setShowAddModal(false);
          }}
          analyzing={analyzing}
        />
      )}

      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
          onUpdate={(updated) => {
            saveJobs(jobs.map(j => j.id === updated.id ? updated : j));
            setSelectedJob(null);
          }}
          onAddToBlacklist={(type, value) => {
            const updated = { ...blacklist };
            if (type === 'email' && !updated.emails.includes(value)) updated.emails.push(value);
            if (type === 'company' && !updated.companies.includes(value)) updated.companies.push(value);
            if (type === 'phone' && !updated.phones.includes(value)) updated.phones.push(value);
            saveBlacklist(updated);
          }}
        />
      )}

      {showBlacklistModal && (
        <BlacklistModal
          blacklist={blacklist}
          onClose={() => setShowBlacklistModal(false)}
          onUpdate={saveBlacklist}
        />
      )}
    </div>
  );
}

// ============================================================================
// STAT CARD (same as before)
// ============================================================================

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    green: 'bg-green-50 text-green-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// LIST VIEW, GRID VIEW, STATS VIEW - Same as before but with ML indicator
// ============================================================================

function ListView({ jobs, onSelect, onDelete }) {
  return (
    <div className="space-y-3">
      {jobs.map(job => {
        const riskLevel = job.riskScore <= 30 ? 'LOW' : job.riskScore <= 60 ? 'MEDIUM' : 'HIGH';
        const risk = RISK_LEVELS[riskLevel];
        const status = STATUS_OPTIONS.find(s => s.value === job.status);

        return (
          <div key={job.id} className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition border border-gray-100">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-start space-x-4">
                  <div className={`mt-1 p-2 rounded-lg bg-${risk.color}-50`}>
                    <risk.icon className={`w-6 h-6 text-${risk.color}-600`} />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium bg-${status.color}-100 text-${status.color}-700`}>
                        {status.label}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium bg-${risk.color}-100 text-${risk.color}-700`}>
                        {risk.label} ({job.riskScore}/100)
                      </span>
                      {job.mlPrediction && (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                          🤖 ML
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-6 text-sm text-gray-600 mb-3">
                      {job.companyName && (
                        <div className="flex items-center space-x-1">
                          <Briefcase className="w-4 h-4" />
                          <span>{job.companyName}</span>
                        </div>
                      )}
                      {job.salary && (
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-4 h-4" />
                          <span>{job.salary}</span>
                        </div>
                      )}
                    </div>

                    {job.riskReasons && job.riskReasons.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <p className="text-sm font-medium text-yellow-800 mb-1">⚠️ Cảnh báo:</p>
                        <ul className="text-sm text-yellow-700 space-y-1">
                          {job.riskReasons.slice(0, 3).map((reason, i) => (
                            <li key={i}>• {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onSelect(job)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                >
                  <Eye className="w-5 h-5" />
                </button>
                <button
                  onClick={() => onDelete(job.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function GridView({ jobs, onSelect, onDelete }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {jobs.map(job => {
        const riskLevel = job.riskScore <= 30 ? 'LOW' : job.riskScore <= 60 ? 'MEDIUM' : 'HIGH';
        const risk = RISK_LEVELS[riskLevel];
        const status = STATUS_OPTIONS.find(s => s.value === job.status);

        return (
          <div key={job.id} className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition border border-gray-100">
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg bg-${risk.color}-50`}>
                <risk.icon className={`w-5 h-5 text-${risk.color}-600`} />
              </div>
              <button
                onClick={() => onDelete(job.id)}
                className="p-1 text-gray-400 hover:text-red-600 transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{job.title}</h3>
            <p className="text-sm text-gray-600 mb-3">{job.companyName}</p>

            <div className="space-y-2 mb-4">
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium bg-${status.color}-100 text-${status.color}-700`}>
                {status.label}
              </span>
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium bg-${risk.color}-100 text-${risk.color}-700 ml-2`}>
                Risk: {job.riskScore}
              </span>
              {job.mlPrediction && (
                <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 ml-2">
                  ML
                </span>
              )}
            </div>

            <button
              onClick={() => onSelect(job)}
              className="w-full py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition text-sm font-medium"
            >
              Xem chi tiết
            </button>
          </div>
        );
      })}
    </div>
  );
}

function StatsView({ jobs }) {
  const riskDistribution = {
    low: jobs.filter(j => j.riskScore <= 30).length,
    medium: jobs.filter(j => j.riskScore > 30 && j.riskScore <= 60).length,
    high: jobs.filter(j => j.riskScore > 60).length
  };

  const statusDistribution = STATUS_OPTIONS.map(s => ({
    label: s.label,
    count: jobs.filter(j => j.status === s.value).length,
    color: s.color
  }));

  const mlCount = jobs.filter(j => j.mlPrediction).length;

  return (
    <div className="grid grid-cols-2 gap-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">Phân bố rủi ro</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Tin cậy</span>
              <span className="text-sm font-medium text-green-600">{riskDistribution.low}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className="bg-green-500 h-3 rounded-full" style={{ width: `${(riskDistribution.low / jobs.length) * 100}%` }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Cần kiểm tra</span>
              <span className="text-sm font-medium text-yellow-600">{riskDistribution.medium}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className="bg-yellow-500 h-3 rounded-full" style={{ width: `${(riskDistribution.medium / jobs.length) * 100}%` }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Nguy cơ cao</span>
              <span className="text-sm font-medium text-red-600">{riskDistribution.high}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className="bg-red-500 h-3 rounded-full" style={{ width: `${(riskDistribution.high / jobs.length) * 100}%` }}></div>
            </div>
          </div>
          <div className="pt-3 border-t">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">🤖 Phân tích bằng ML</span>
              <span className="text-sm font-medium text-purple-600">{mlCount}/{jobs.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">Trạng thái apply</h3>
        <div className="space-y-3">
          {statusDistribution.map(s => (
            <div key={s.label} className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{s.label}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${s.color}-100 text-${s.color}-700`}>
                {s.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// ADD JOB MODAL, JOB DETAIL MODAL, BLACKLIST MODAL
// Copy from previous version with minor updates
// ============================================================================

function AddJobModal({ onClose, onSave, analyzing }) {
  const [formData, setFormData] = useState({
    title: '',
    companyName: '',
    description: '',
    salary: '',
    address: '',
    email: '',
    phone: '',
    url: '',
    status: 'considering'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Thêm tin tuyển dụng mới</h2>
          <p className="text-sm text-gray-600 mt-1">Hệ thống sẽ tự động phân tích rủi ro bằng AI</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vị trí tuyển dụng *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="VD: Senior Frontend Developer"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tên công ty</label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mức lương</label>
              <input
                type="text"
                value={formData.salary}
                onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: 15-20 triệu"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả công việc</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Địa chỉ</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email liên hệ</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Link tin tuyển dụng</label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
              disabled={analyzing}
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={analyzing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center space-x-2"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Đang phân tích...</span>
                </>
              ) : (
                <span>Lưu tin</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// JobDetailModal and BlacklistModal same as before...
function JobDetailModal({ job, onClose, onUpdate, onAddToBlacklist }) {
  const [formData, setFormData] = useState(job);
  const [personalNote, setPersonalNote] = useState(job.personalNote || '');
  const [rating, setRating] = useState(job.rating || 0);

  const riskLevel = job.riskScore <= 30 ? 'LOW' : job.riskScore <= 60 ? 'MEDIUM' : 'HIGH';
  const risk = RISK_LEVELS[riskLevel];

  const handleSave = () => {
    onUpdate({ ...formData, personalNote, rating });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Chi tiết tin tuyển dụng</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div className="p-6 space-y-6">
          {/* Risk Score */}
          <div className={`bg-${risk.color}-50 border border-${risk.color}-200 rounded-lg p-4`}>
            <div className="flex items-center space-x-3 mb-3">
              <risk.icon className={`w-8 h-8 text-${risk.color}-600`} />
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className={`text-lg font-semibold text-${risk.color}-900`}>{risk.label}</h3>
                  {job.mlPrediction && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                      🤖 ML Prediction
                    </span>
                  )}
                </div>
                <p className={`text-sm text-${risk.color}-700`}>Điểm rủi ro: {job.riskScore}/100</p>
              </div>
            </div>
            {job.riskReasons && job.riskReasons.length > 0 && (
              <div>
                <p className={`text-sm font-medium text-${risk.color}-800 mb-2`}>Lý do:</p>
                <ul className={`text-sm text-${risk.color}-700 space-y-1`}>
                  {job.riskReasons.map((reason, i) => (
                    <li key={i}>• {reason}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Job Info */}
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900 text-lg">{job.title}</h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center space-x-2 text-gray-600">
                <Briefcase className="w-4 h-4" />
                <span>{job.companyName || 'Chưa rõ'}</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-600">
                <DollarSign className="w-4 h-4" />
                <span>{job.salary || 'Thỏa thuận'}</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>{job.address || 'Chưa rõ'}</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-600">
                <Mail className="w-4 h-4" />
                <span>{job.email || 'Chưa rõ'}</span>
              </div>
            </div>

            {job.description && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-700">{job.description}</p>
              </div>
            )}
          </div>

          {/* Personal Notes */}
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3">Ghi chú cá nhân</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Đánh giá sao</label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map(star => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className={`text-2xl ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú</label>
                <textarea
                  value={personalNote}
                  onChange={(e) => setPersonalNote(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lưu
              </button>
            </div>
          </div>

          {/* Blacklist Actions */}
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3">Thêm vào danh sách đen</h4>
            <div className="flex flex-wrap gap-2">
              {job.email && (
                <button
                  onClick={() => onAddToBlacklist('email', job.email)}
                  className="px-3 py-1 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-sm"
                >
                  + Email: {job.email}
                </button>
              )}
              {job.companyName && (
                <button
                  onClick={() => onAddToBlacklist('company', job.companyName)}
                  className="px-3 py-1 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-sm"
                >
                  + Công ty: {job.companyName}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BlacklistModal({ blacklist, onClose, onUpdate }) {
  const [newEmail, setNewEmail] = useState('');
  const [newCompany, setNewCompany] = useState('');
  const [newPhone, setNewPhone] = useState('');

  const handleAdd = (type, value) => {
    if (!value.trim()) return;
    
    const updated = { ...blacklist };
    if (type === 'email') updated.emails.push(value.trim());
    if (type === 'company') updated.companies.push(value.trim());
    if (type === 'phone') updated.phones.push(value.trim());
    
    onUpdate(updated);
    
    if (type === 'email') setNewEmail('');
    if (type === 'company') setNewCompany('');
    if (type === 'phone') setNewPhone('');
  };

  const handleRemove = (type, index) => {
    const updated = { ...blacklist };
    if (type === 'email') updated.emails.splice(index, 1);
    if (type === 'company') updated.companies.splice(index, 1);
    if (type === 'phone') updated.phones.splice(index, 1);
    onUpdate(updated);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-6 h-6 text-red-600" />
            <h2 className="text-2xl font-bold text-gray-900">Danh sách đen</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div className="p-6 space-y-6">
          {/* Email Blacklist */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Email nghi ngờ</h3>
            <div className="flex space-x-2 mb-3">
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="Nhập email..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => handleAdd('email', newEmail)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Thêm
              </button>
            </div>
            <div className="space-y-2">
              {blacklist.emails.map((email, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 px-4 py-2 rounded-lg">
                  <span className="text-sm text-gray-700">{email}</span>
                  <button
                    onClick={() => handleRemove('email', i)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {blacklist.emails.length === 0 && (
                <p className="text-sm text-gray-500 italic">Chưa có email nào</p>
              )}
            </div>
          </div>

          {/* Company Blacklist */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Công ty không tin cậy</h3>
            <div className="flex space-x-2 mb-3">
              <input
                type="text"
                value={newCompany}
                onChange={(e) => setNewCompany(e.target.value)}
                placeholder="Nhập tên công ty..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => handleAdd('company', newCompany)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Thêm
              </button>
            </div>
            <div className="space-y-2">
              {blacklist.companies.map((company, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 px-4 py-2 rounded-lg">
                  <span className="text-sm text-gray-700">{company}</span>
                  <button
                    onClick={() => handleRemove('company', i)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {blacklist.companies.length === 0 && (
                <p className="text-sm text-gray-500 italic">Chưa có công ty nào</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
