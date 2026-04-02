import { useEffect, useState } from "react";
import { api } from "./api";
import { sampleJob, sampleProfile } from "./mockData";

const menu = [
  { id: "overview", label: "Tổng quan" },
  { id: "jobs", label: "Quản lý tin" },
  { id: "analyze", label: "Đánh giá tin cậy" },
  { id: "recommend", label: "Cá nhân hóa" },
  { id: "blacklist", label: "Blacklist" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobTotal, setJobTotal] = useState(0);
  const [jobPage, setJobPage] = useState(1);
  const [jobPageSize] = useState(12);
  const [jobTotalPages, setJobTotalPages] = useState(0);
  const [jobQuery, setJobQuery] = useState("");
  const [jobRisk, setJobRisk] = useState("ALL");
  const [analysisInput, setAnalysisInput] = useState(sampleJob);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [profileInput, setProfileInput] = useState(sampleProfile);
  const [recommendations, setRecommendations] = useState([]);
  const [blacklist, setBlacklist] = useState({ companies: [], emails: [], phones: [] });
  const [status, setStatus] = useState("Đang tải dữ liệu...");

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadJobs();
  }, [jobRisk, jobPage]);

  async function loadInitialData() {
    try {
      const [overviewData, jobsData, blacklistData] = await Promise.all([
        api.getOverview(),
        api.getJobs({ page: 1, pageSize: jobPageSize }),
        api.getBlacklist(),
      ]);
      setOverview(overviewData);
      setJobs(jobsData.items);
      setJobTotal(jobsData.total);
      setJobPage(jobsData.page ?? 1);
      setJobTotalPages(jobsData.totalPages ?? 0);
      setBlacklist(blacklistData);
      setStatus("Hệ thống sẵn sàng.");
    } catch (error) {
      setStatus("Không kết nối được backend Flask. Vui lòng chạy server ở cổng 5000.");
    }
  }

  async function loadJobs() {
    try {
      const data = await api.getJobs({
        query: jobQuery,
        risk: jobRisk,
        page: jobPage,
        pageSize: jobPageSize,
      });
      setJobs(data.items);
      setJobTotal(data.total);
      setJobPage(data.page ?? 1);
      setJobTotalPages(data.totalPages ?? 0);
    } catch (error) {
      setJobs([]);
      setJobTotal(0);
      setJobTotalPages(0);
    }
  }

  function handleJobSearch() {
    setJobPage(1);
    if (jobPage === 1) {
      loadJobs();
    }
  }

  async function handleAnalyze(event) {
    event.preventDefault();
    const result = await api.analyzeJob({
      ...analysisInput,
      candidateProfile: buildProfilePayload(profileInput),
    });
    setAnalysisResult(result);
    setActiveTab("analyze");
  }

  async function handleRecommend() {
    const result = await api.recommend(buildProfilePayload(profileInput));
    setRecommendations(result.items || []);
  }

  async function handleBlacklistSave() {
    const updated = await api.updateBlacklist(blacklist);
    setBlacklist(updated);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
       
          <h1>JobTrust AI</h1>
          <p className="muted">
            Hệ thống quản lý và đánh giá độ tin cậy tin tuyển dụng cá nhân hóa ứng dụng Machine Learning.
          </p>
        </div>

        <nav className="menu">
          {menu.map((item) => (
            <button
              key={item.id}
              className={activeTab === item.id ? "menu-item active" : "menu-item"}
              onClick={() => setActiveTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="status-card">
          <span className="status-dot" />
          <div>
            <strong>Trạng thái hệ thống</strong>
            <p>{status}</p>
          </div>
        </div>
      </aside>

      <main className="content">
        <section className="hero">
          <div>
            <h2>Trực quan hóa rủi ro, blacklist và gợi ý việc làm an toàn cho từng ứng viên.</h2>
          </div>
          <button className="primary-btn" onClick={() => setActiveTab("analyze")}>
            Đánh giá tin ngay
          </button>
        </section>

        {activeTab === "overview" && <OverviewPanel overview={overview} />}
        {activeTab === "jobs" && (
          <JobsPanel
            jobs={jobs}
            total={jobTotal}
            page={jobPage}
            pageSize={jobPageSize}
            totalPages={jobTotalPages}
            jobQuery={jobQuery}
            setJobQuery={setJobQuery}
            jobRisk={jobRisk}
            setJobRisk={(value) => {
              setJobRisk(value);
              setJobPage(1);
            }}
            onSearch={handleJobSearch}
            onPreviousPage={() => setJobPage((current) => Math.max(1, current - 1))}
            onNextPage={() => setJobPage((current) => Math.min(jobTotalPages || 1, current + 1))}
          />
        )}
        {activeTab === "analyze" && (
          <AnalyzePanel
            input={analysisInput}
            setInput={setAnalysisInput}
            result={analysisResult}
            onSubmit={handleAnalyze}
          />
        )}
        {activeTab === "recommend" && (
          <RecommendPanel
            profile={profileInput}
            setProfile={setProfileInput}
            items={recommendations}
            onRecommend={handleRecommend}
          />
        )}
        {activeTab === "blacklist" && (
          <BlacklistPanel blacklist={blacklist} setBlacklist={setBlacklist} onSave={handleBlacklistSave} />
        )}
      </main>
    </div>
  );
}

function buildProfilePayload(profile) {
  const keywords =
    typeof profile.keywordsText === "string"
      ? profile.keywordsText
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      : profile.keywords || [];

  return {
    ...profile,
    keywords,
  };
}

function formatDisplayTitle(title) {
  if (!title) return "Tin tuyển dụng";

  return String(title)
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map((word) => {
      if (!word) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

function OverviewPanel({ overview }) {
  if (!overview) {
    return <div className="panel">Đang tải thống kê...</div>;
  }

  return (
    <div className="panel-grid">
      <div className="stats-grid">
        <StatCard title="Tổng tin hợp lệ" value={overview.summary.totalJobs} accent="blue" />
        <StatCard title="Rủi ro thấp" value={overview.summary.lowRiskJobs} accent="green" />
        <StatCard title="Rủi ro trung bình" value={overview.summary.mediumRiskJobs} accent="amber" />
        <StatCard title="Rủi ro cao" value={overview.summary.highRiskJobs} accent="red" />
      </div>

      <div className="panel">
        <h3>Phân bố rủi ro</h3>
        <div className="bar-list">
          {overview.charts.riskDistribution.map((item) => (
            <BarRow key={item.label} label={item.label} value={item.value} max={overview.summary.totalJobs || 1} />
          ))}
        </div>
      </div>

      <div className="panel">
        <h3>Doanh nghiệp xuất hiện nhiều</h3>
        <div className="list">
          {overview.charts.topCompanies.map((company) => (
            <div key={company.name} className="list-row">
              <span>{company.name}</span>
              <strong>{company.value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h3>Tín hiệu cảnh báo phổ biến</h3>
        <div className="list">
          {overview.charts.topReasons.map((reason) => (
            <div key={reason.reason} className="list-row">
              <span>{reason.reason}</span>
              <strong>{reason.value}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function JobsPanel({
  jobs,
  total,
  page,
  pageSize,
  totalPages,
  jobQuery,
  setJobQuery,
  jobRisk,
  setJobRisk,
  onSearch,
  onPreviousPage,
  onNextPage,
}) {
  return (
    <section className="panel-grid">
      <div className="panel filter-panel">
        <div>
          <h3>Quản lý kho tin tuyển dụng</h3>
          <p className="muted">Tìm kiếm theo nội dung và lọc theo mức rủi ro để phục vụ quản trị.</p>
        </div>
        <div className="filters">
          <input value={jobQuery} onChange={(e) => setJobQuery(e.target.value)} placeholder="Tìm theo tên công ty, tiêu đề..." />
          <select value={jobRisk} onChange={(e) => setJobRisk(e.target.value)}>
            <option value="ALL">Tất cả mức rủi ro</option>
            <option value="LOW">Rủi ro thấp</option>
            <option value="MEDIUM">Rủi ro trung bình</option>
            <option value="HIGH">Rủi ro cao</option>
          </select>
          <button className="primary-btn" onClick={onSearch}>Lọc dữ liệu</button>
        </div>
        <div className="pagination-summary">
          <p className="muted">Tổng kết quả: {total}</p>
          <p className="muted">
            Trang {total === 0 ? 0 : page}/{totalPages || 0} • {pageSize} tin mỗi trang
          </p>
        </div>
      </div>

      <div className="jobs-grid">
        {jobs.map((job) => (
          <article key={job.id} className="job-card">
            <div className="job-card-top">
              <span className={`pill ${job.riskLevel.toLowerCase()}`}>{job.riskLevel}</span>
              <strong>{job.trustScore}% tin cậy</strong>
            </div>
            <p><strong>Vị trí tuyển dụng:</strong></p>
            <h4>{formatDisplayTitle(job.title)}</h4>
            <div className="meta-grid">
              <span><strong>Tên công ty:</strong> {job.companyName || "Chưa rõ công ty"}</span>
              <span><strong>Mức lương:</strong> {job.salary || "Đang cập nhật lương"}</span>
              <span><strong>Khu vực:</strong> {job.location}</span>
              <span><strong>Độ tin cậy mô hình:</strong> {job.confidence}</span>
            </div>
          </article>
        ))}
      </div>

      <div className="panel pagination-panel">
        <button className="secondary-btn" onClick={onPreviousPage} disabled={page <= 1}>
          Trang trước
        </button>
        <span className="pagination-text">
          Trang {total === 0 ? 0 : page} / {totalPages || 0}
        </span>
        <button className="secondary-btn" onClick={onNextPage} disabled={totalPages === 0 || page >= totalPages}>
          Trang sau
        </button>
      </div>
    </section>
  );
}

function AnalyzePanel({ input, setInput, result, onSubmit }) {
  const fields = [
    ["title", "Tiêu đề tin"],
    ["companyName", "Tên công ty"],
    ["salary", "Mức lương"],
    ["address", "Địa chỉ"],
    ["email", "Email"],
    ["phone", "Số điện thoại"],
    ["companySize", "Quy mô công ty"],
    ["experience", "Kinh nghiệm"],
  ];

  return (
    <section className="panel-grid double">
      <form className="panel form-panel" onSubmit={onSubmit}>
        <h3>Phân tích độ tin cậy tin tuyển dụng</h3>
        <div className="form-grid">
          {fields.map(([key, label]) => (
            <label key={key}>
              <span>{label}</span>
              <input value={input[key]} onChange={(e) => setInput({ ...input, [key]: e.target.value })} />
            </label>
          ))}
          <label className="full">
            <span>Mô tả công việc</span>
            <textarea rows="5" value={input.description} onChange={(e) => setInput({ ...input, description: e.target.value })} />
          </label>
          <label className="full">
            <span>Yêu cầu</span>
            <textarea rows="4" value={input.requirements} onChange={(e) => setInput({ ...input, requirements: e.target.value })} />
          </label>
          <label className="full">
            <span>Phúc lợi</span>
            <textarea rows="3" value={input.benefits} onChange={(e) => setInput({ ...input, benefits: e.target.value })} />
          </label>
        </div>
        <button className="primary-btn" type="submit">Chấm điểm tin tuyển dụng</button>
      </form>

      <div className="panel result-panel">
        <h3>Kết quả đánh giá</h3>
        {!result && <p className="muted">Nhập dữ liệu và bấm chấm điểm để xem kết quả từ model và heuristic.</p>}
        {result && (
          <>
            <div className="stats-grid compact">
              <StatCard title="Trust Score" value={`${result.result.trustScore}%`} accent="green" />
              <StatCard title="Risk Score" value={`${result.result.riskScore}%`} accent="red" />
              <StatCard title="Mức rủi ro" value={result.result.riskLevel} accent="amber" />
              <StatCard title="Độ tự tin" value={result.result.confidence} accent="blue" />
            </div>
            <div className="detail-block">
              <h4>Quyết định</h4>
              <p>{result.result.decision}</p>
            </div>
            <div className="detail-block">
              <h4>Tín hiệu cảnh báo</h4>
              <ul>
                {(result.signals || []).map((signal) => (
                  <li key={signal}>{signal}</li>
                ))}
              </ul>
            </div>
            <div className="detail-block">
              <h4>Blacklist</h4>
              <p>{result.blacklist.hasMatch ? result.blacklist.details.join(" | ") : "Không có trùng khớp."}</p>
            </div>
            <div className="detail-block">
              <h4>Độ phù hợp cá nhân hóa</h4>
              <p>Fit Score: {result.personalization.fitScore}</p>
              <p>Từ khóa phù hợp: {(result.personalization.matchedKeywords || []).join(", ") || "Chưa có"}</p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function RecommendPanel({ profile, setProfile, items, onRecommend }) {
  return (
    <section className="panel-grid double">
      <div className="panel">
        <h3>Cá nhân hóa việc làm an toàn</h3>
        <p className="muted">Kết hợp độ tin cậy và sở thích ứng viên để gợi ý tin phù hợp.</p>
        <label>
          <span>Họ tên</span>
          <input value={profile.fullName} onChange={(e) => setProfile({ ...profile, fullName: e.target.value })} />
        </label>
        <label>
          <span>Từ khóa nghề nghiệp</span>
          <textarea
            rows="4"
            value={profile.keywordsText ?? ""}
            onChange={(e) => setProfile({ ...profile, keywordsText: e.target.value })}
          />
        </label>
        <button className="primary-btn" onClick={onRecommend}>Lấy gợi ý cá nhân hóa</button>
      </div>

      <div className="panel">
        <h3>Danh sách đề xuất</h3>
        <div className="list">
          {items.map((item) => (
            <div key={item.id} className="recommend-card">
              <div className="job-card-top">
                <span className={`pill ${item.riskLevel.toLowerCase()}`}>{item.riskLevel}</span>
                <strong>{item.personalizationScore} điểm phù hợp</strong>
              </div>
              <p><strong>Vị trí tuyển dụng:</strong></p>
              <h4>{formatDisplayTitle(item.title)}</h4>
              <p><strong>Tên công ty:</strong> {item.companyName}</p>
              <p><strong>Mức lương:</strong> {item.salary || "Đang cập nhật lương"}</p>
              <p><strong>Khu vực:</strong> {item.location}</p>
              <p><strong>Từ khóa trùng:</strong> {(item.matchedKeywords || []).join(", ") || "Không có"}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function BlacklistPanel({ blacklist, setBlacklist, onSave }) {
  return (
    <section className="panel-grid double">
      <div className="panel">
        <h3>Quản lý blacklist</h3>
        <p className="muted">Bổ sung email, công ty và số điện thoại cần cảnh báo cho hệ thống.</p>
        <label>
          <span>Công ty</span>
          <textarea rows="5" value={blacklist.companies.join("\n")} onChange={(e) => setBlacklist({ ...blacklist, companies: e.target.value.split("\n").filter(Boolean) })} />
        </label>
        <label>
          <span>Email</span>
          <textarea rows="5" value={blacklist.emails.join("\n")} onChange={(e) => setBlacklist({ ...blacklist, emails: e.target.value.split("\n").filter(Boolean) })} />
        </label>
        <label>
          <span>Số điện thoại</span>
          <textarea rows="5" value={blacklist.phones.join("\n")} onChange={(e) => setBlacklist({ ...blacklist, phones: e.target.value.split("\n").filter(Boolean) })} />
        </label>
        <button className="primary-btn" onClick={onSave}>Lưu blacklist</button>
      </div>

      <div className="panel">
        <h3>Giá trị demo</h3>
        <div className="list">
          <div className="list-row"><span>Số công ty cảnh báo</span><strong>{blacklist.companies.length}</strong></div>
          <div className="list-row"><span>Số email cảnh báo</span><strong>{blacklist.emails.length}</strong></div>
          <div className="list-row"><span>Số điện thoại cảnh báo</span><strong>{blacklist.phones.length}</strong></div>
        </div>
      </div>
    </section>
  );
}

function StatCard({ title, value, accent }) {
  return (
    <div className={`stat-card ${accent}`}>
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

function BarRow({ label, value, max }) {
  const width = `${Math.max(10, (value / max) * 100)}%`;
  return (
    <div className="bar-row">
      <div className="bar-row-header">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width }} />
      </div>
    </div>
  );
}
