import { useEffect, useState } from "react";
import { api } from "./api";
import { sampleBatchText, sampleJob, sampleProfile } from "./mockData";

const menu = [
  { id: "overview", label: "Tổng quan" },
  { id: "jobs", label: "Quản lý tin" },
  { id: "analyze", label: "Đánh giá tin cậy" },
  { id: "batch", label: "Đánh giá hàng loạt" },
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
  const [analysisErrors, setAnalysisErrors] = useState({});
  const [batchInput, setBatchInput] = useState(sampleBatchText);
  const [batchErrors, setBatchErrors] = useState({});
  const [batchResult, setBatchResult] = useState(null);
  const [profileInput, setProfileInput] = useState(sampleProfile);
  const [profileErrors, setProfileErrors] = useState({});
  const [recommendations, setRecommendations] = useState([]);
  const [blacklist, setBlacklist] = useState({ companies: [], emails: [], phones: [] });
  const [blacklistInput, setBlacklistInput] = useState({
    companiesText: "",
    emailsText: "",
    phonesText: "",
  });
  const [blacklistErrors, setBlacklistErrors] = useState({});
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
      setBlacklistInput(buildBlacklistInput(blacklistData));
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
    const errors = validateAnalysisInput(analysisInput);
    setAnalysisErrors(errors);
    if (Object.keys(errors).length > 0) {
      setStatus("Vui lòng kiểm tra lại thông tin trong biểu mẫu phân tích.");
      return;
    }

    const result = await api.analyzeJob({
      ...analysisInput,
      candidateProfile: buildProfilePayload(profileInput),
    });
    setAnalysisResult(result);
    setActiveTab("analyze");
  }

  async function handleRecommend() {
    const errors = validateProfileInput(profileInput);
    setProfileErrors(errors);
    if (Object.keys(errors).length > 0) {
      setStatus("Vui lòng kiểm tra lại hồ sơ cá nhân hóa.");
      return;
    }

    const result = await api.recommend(buildProfilePayload(profileInput));
    setRecommendations(result.items || []);
  }

  async function handleBatchAnalyze() {
    const errors = validateBatchInput(batchInput);
    setBatchErrors(errors);
    if (Object.keys(errors).length > 0) {
      setStatus("Vui lòng kiểm tra lại dữ liệu batch trước khi phân tích.");
      return;
    }

    const result = await api.batchAnalyze({ rawText: batchInput });
    setBatchResult(result);
    setStatus(`Đã phân tích ${result.summary?.total || 0} tin tuyển dụng từ dữ liệu dán vào.`);
  }

  async function handleBlacklistSave() {
    const parsedBlacklist = buildBlacklistPayload(blacklistInput);
    const errors = validateBlacklistInput(parsedBlacklist);
    setBlacklistErrors(errors);
    if (Object.keys(errors).length > 0) {
      setStatus("Blacklist có dữ liệu chưa hợp lệ, vui lòng kiểm tra lại.");
      return;
    }

    const updated = await api.updateBlacklist(parsedBlacklist);
    setBlacklist(updated);
    setBlacklistInput(buildBlacklistInput(updated));
    setStatus("Đã lưu blacklist thành công.");
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
            errors={analysisErrors}
            setErrors={setAnalysisErrors}
            result={analysisResult}
            onSubmit={handleAnalyze}
          />
        )}
        {activeTab === "batch" && (
          <BatchAnalyzePanel
            batchInput={batchInput}
            setBatchInput={setBatchInput}
            batchErrors={batchErrors}
            setBatchErrors={setBatchErrors}
            batchResult={batchResult}
            onBatchAnalyze={handleBatchAnalyze}
          />
        )}
        {activeTab === "recommend" && (
          <RecommendPanel
            profile={profileInput}
            setProfile={setProfileInput}
            errors={profileErrors}
            setErrors={setProfileErrors}
            items={recommendations}
            onRecommend={handleRecommend}
          />
        )}
        {activeTab === "blacklist" && (
          <BlacklistPanel
            blacklist={blacklist}
            input={blacklistInput}
            setInput={setBlacklistInput}
            errors={blacklistErrors}
            setErrors={setBlacklistErrors}
            onSave={handleBlacklistSave}
          />
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

function buildBlacklistInput(blacklist) {
  return {
    companiesText: (blacklist.companies || []).join("\n"),
    emailsText: (blacklist.emails || []).join("\n"),
    phonesText: (blacklist.phones || []).join("\n"),
  };
}

function buildBlacklistPayload(input) {
  return {
    companies: splitLines(input.companiesText),
    emails: splitLines(input.emailsText),
    phones: splitLines(input.phonesText),
  };
}

function splitLines(value) {
  return String(value || "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function validateAnalysisInput(input) {
  const errors = {};
  if (!input.title.trim()) errors.title = "Vui lòng nhập vị trí tuyển dụng.";
  if (!input.companyName.trim()) errors.companyName = "Vui lòng nhập tên công ty.";
  if (!input.description.trim()) errors.description = "Vui lòng nhập mô tả công việc.";
  if (input.description.trim().length < 30) errors.description = "Mô tả cần ít nhất 30 ký tự.";
  if (input.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email)) errors.email = "Email chưa đúng định dạng.";
  if (input.phone && !/^[0-9+\s().-]{8,20}$/.test(input.phone)) errors.phone = "Số điện thoại chưa đúng định dạng.";
  if (input.salary && !/[0-9]/.test(input.salary)) errors.salary = "Mức lương nên có số hoặc khoảng lương cụ thể.";
  return errors;
}

function validateProfileInput(profile) {
  const errors = {};
  if (!String(profile.fullName || "").trim()) errors.fullName = "Vui lòng nhập họ tên.";
  if (!String(profile.keywordsText || "").trim()) errors.keywordsText = "Vui lòng nhập ít nhất một từ khóa nghề nghiệp.";
  return errors;
}

function validateBatchInput(rawText) {
  const errors = {};
  if (!String(rawText || "").trim()) {
    errors.rawText = "Vui lòng dán dữ liệu nhiều tin tuyển dụng.";
    return errors;
  }

  const blocks = String(rawText).split(/\n\s*\n+/).filter((item) => item.trim());
  if (blocks.length > 50) {
    errors.rawText = "Chỉ hỗ trợ tối đa 50 tin trong một lần phân tích.";
  }
  return errors;
}

function validateBlacklistInput(blacklist) {
  const errors = {};
  const invalidEmails = blacklist.emails.filter((email) => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email));
  const invalidPhones = blacklist.phones.filter((phone) => !/^[0-9+\s().-]{8,20}$/.test(phone));
  if (invalidEmails.length > 0) errors.emailsText = "Có email chưa đúng định dạng trong blacklist.";
  if (invalidPhones.length > 0) errors.phonesText = "Có số điện thoại chưa đúng định dạng trong blacklist.";
  return errors;
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

function AnalyzePanel({
  input,
  setInput,
  errors,
  setErrors,
  result,
  onSubmit,
}) {
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

  function updateField(key, value) {
    setInput({ ...input, [key]: value });
    if (errors[key]) {
      setErrors({ ...errors, [key]: "" });
    }
  }

  return (
    <section className="panel-grid double">
      <form className="panel form-panel" onSubmit={onSubmit}>
        <h3>Phân tích độ tin cậy tin tuyển dụng</h3>
        <div className="form-grid">
          {fields.map(([key, label]) => (
            <label key={key}>
              <span>{label}</span>
              <input
                value={input[key]}
                onChange={(e) => updateField(key, e.target.value)}
                className={errors[key] ? "input-error" : ""}
              />
              {errors[key] && <small className="error-text">{errors[key]}</small>}
            </label>
          ))}
          <label className="full">
            <span>Mô tả công việc</span>
            <textarea
              rows="5"
              value={input.description}
              onChange={(e) => updateField("description", e.target.value)}
              className={errors.description ? "input-error" : ""}
            />
            {errors.description && <small className="error-text">{errors.description}</small>}
          </label>
          <label className="full">
            <span>Yêu cầu</span>
            <textarea rows="4" value={input.requirements} onChange={(e) => updateField("requirements", e.target.value)} />
          </label>
          <label className="full">
            <span>Phúc lợi</span>
            <textarea rows="3" value={input.benefits} onChange={(e) => updateField("benefits", e.target.value)} />
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

function BatchAnalyzePanel({
  batchInput,
  setBatchInput,
  batchErrors,
  setBatchErrors,
  batchResult,
  onBatchAnalyze,
}) {
  return (
    <section className="panel-grid double">
      <div className="panel form-panel">
        <h3>Đánh giá nhiều tin cùng lúc</h3>
        <p className="muted">
          Bạn có thể dán dữ liệu lộn xộn. Hệ thống sẽ cố gắng tách tự động theo từng khối, mỗi tin cách nhau một dòng trống.
        </p>
        <label className="full">
          <span>Dữ liệu nhiều tin tuyển dụng</span>
          <textarea
            rows="18"
            value={batchInput}
            onChange={(e) => {
              setBatchInput(e.target.value);
              if (batchErrors.rawText) {
                setBatchErrors({});
              }
            }}
            className={batchErrors.rawText ? "input-error" : ""}
          />
          <small className="helper-text">
            Mẫu gợi ý: `Vị trí: ...`, `Tên công ty: ...`, `Mức lương: ...`, `Email: ...`, `Mô tả: ...`
          </small>
          {batchErrors.rawText && <small className="error-text">{batchErrors.rawText}</small>}
        </label>
        <button className="primary-btn" type="button" onClick={onBatchAnalyze}>Phân tích hàng loạt</button>
      </div>

      <div className="panel result-panel">
        <h3>Kết quả phân tích hàng loạt</h3>
        {!batchResult && <p className="muted">Dán nhiều tin tuyển dụng để xem thống kê và danh sách kết quả.</p>}
        {batchResult && (
          <>
            <div className="stats-grid compact">
              <StatCard title="Số tin đã phân tích" value={batchResult.summary.total} accent="blue" />
              <StatCard title="Trust Score TB" value={batchResult.summary.averageTrustScore} accent="green" />
              <StatCard title="Rủi ro thấp" value={batchResult.summary.riskLevelsVi?.["Thấp"] || 0} accent="amber" />
              <StatCard title="Rủi ro cao" value={batchResult.summary.riskLevelsVi?.["Cao"] || 0} accent="red" />
            </div>
            <div className="detail-block">
              <h4>Thống kê tổng hợp</h4>
              <p>
                Phân bố rủi ro: Thấp {batchResult.summary.riskLevelsVi?.["Thấp"] || 0} • Trung bình {batchResult.summary.riskLevelsVi?.["Trung bình"] || 0} • Cao {batchResult.summary.riskLevelsVi?.["Cao"] || 0}
              </p>
              <p>Số khối dữ liệu đã tách: {batchResult.summary.parsedFromText || 0}</p>
            </div>
            {batchResult.parsingNotes?.length > 0 && (
              <div className="detail-block">
                <h4>Ghi chú tách dữ liệu</h4>
                <ul>
                  {batchResult.parsingNotes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="batch-result-list">
              {batchResult.items?.map((item, index) => (
                <div key={`${item.job.title}-${index}`} className="batch-result-card">
                  <div className="job-card-top">
                    <span className={`pill ${item.result.riskLevel.toLowerCase()}`}>{item.result.riskLabel || item.result.riskLevel}</span>
                    <strong>{item.result.trustScore}% tin cậy</strong>
                  </div>
                  <p><strong>Vị trí:</strong> {item.job.title || "Chưa rõ"}</p>
                  <p><strong>Công ty:</strong> {item.job.companyName || "Chưa rõ"}</p>
                  <p><strong>Kết luận:</strong> {item.result.decision}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function RecommendPanel({ profile, setProfile, errors, setErrors, items, onRecommend }) {
  function updateProfileField(key, value) {
    setProfile({ ...profile, [key]: value });
    if (errors[key]) {
      setErrors({ ...errors, [key]: "" });
    }
  }

  return (
    <section className="panel-grid double">
      <div className="panel">
        <h3>Cá nhân hóa việc làm an toàn</h3>
        <p className="muted">Kết hợp độ tin cậy và sở thích ứng viên để gợi ý tin phù hợp.</p>
        <label>
          <span>Họ tên</span>
          <input
            value={profile.fullName}
            onChange={(e) => updateProfileField("fullName", e.target.value)}
            className={errors.fullName ? "input-error" : ""}
          />
          {errors.fullName && <small className="error-text">{errors.fullName}</small>}
        </label>
        <label>
          <span>Từ khóa nghề nghiệp</span>
          <textarea
            rows="4"
            value={profile.keywordsText ?? ""}
            onChange={(e) => updateProfileField("keywordsText", e.target.value)}
            className={errors.keywordsText ? "input-error" : ""}
          />
          {errors.keywordsText && <small className="error-text">{errors.keywordsText}</small>}
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

function BlacklistPanel({ blacklist, input, setInput, errors, setErrors, onSave }) {
  function updateBlacklistField(key, value) {
    setInput({ ...input, [key]: value });
    if (errors[key]) {
      setErrors({ ...errors, [key]: "" });
    }
  }

  return (
    <section className="panel-grid double">
      <div className="panel">
        <h3>Quản lý blacklist</h3>
        <p className="muted">Bổ sung email, công ty và số điện thoại cần cảnh báo cho hệ thống.</p>
        <label>
          <span>Công ty</span>
          <textarea rows="8" value={input.companiesText} onChange={(e) => updateBlacklistField("companiesText", e.target.value)} />
          <small className="helper-text">Mỗi dòng là một công ty. Hệ thống sẽ tự loại bỏ mục trùng lặp khi lưu.</small>
          <small className="count-text">Đã nhập: {splitLines(input.companiesText).length} công ty</small>
        </label>
        <label>
          <span>Email</span>
          <textarea
            rows="8"
            value={input.emailsText}
            onChange={(e) => updateBlacklistField("emailsText", e.target.value)}
            className={errors.emailsText ? "input-error" : ""}
          />
          <small className="helper-text">Mỗi dòng là một email. Ví dụ: `abc@company.com`</small>
          <small className="count-text">Đã nhập: {splitLines(input.emailsText).length} email</small>
          {errors.emailsText && <small className="error-text">{errors.emailsText}</small>}
        </label>
        <label>
          <span>Số điện thoại</span>
          <textarea
            rows="8"
            value={input.phonesText}
            onChange={(e) => updateBlacklistField("phonesText", e.target.value)}
            className={errors.phonesText ? "input-error" : ""}
          />
          <small className="helper-text">Mỗi dòng là một số điện thoại. Có thể nhập `0909...` hoặc `+84...`</small>
          <small className="count-text">Đã nhập: {splitLines(input.phonesText).length} số điện thoại</small>
          {errors.phonesText && <small className="error-text">{errors.phonesText}</small>}
        </label>
        <button className="primary-btn" onClick={onSave}>Lưu blacklist</button>
      </div>

      <div className="panel">
        <h3>Dữ liệu đã lưu</h3>
        <div className="list">
          <div className="list-row"><span>Số công ty cảnh báo</span><strong>{blacklist.companies.length}</strong></div>
          <div className="list-row"><span>Số email cảnh báo</span><strong>{blacklist.emails.length}</strong></div>
          <div className="list-row"><span>Số điện thoại cảnh báo</span><strong>{blacklist.phones.length}</strong></div>
        </div>
        <p className="muted">Bạn có thể dán cả danh sách dài, mỗi mục trên một dòng. Khi lưu, hệ thống sẽ tự chuẩn hóa và loại bỏ dữ liệu trùng.</p>
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
