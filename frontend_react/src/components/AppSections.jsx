import { useEffect, useState } from "react";

function Field({
  label,
  type = "text",
  value,
  onChange,
  error,
  autoComplete,
  maxLength,
  minLength,
  inputMode,
  required = false,
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={error ? "input-error" : ""}
        autoComplete={autoComplete}
        maxLength={maxLength}
        minLength={minLength}
        inputMode={inputMode}
        required={required}
      />
      {error && <small className="error-text">{error}</small>}
    </label>
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

function DetailItem({ label, value, multiline = false, longText = false }) {
  const displayValue = value === undefined || value === null || value === "" ? "Không có " : value;
  return (
    <div className={`detail-item${multiline ? " detail-item-wide" : ""}${longText ? " detail-item-rich" : ""}`}>
      <span>{label}</span>
      <strong>{displayValue}</strong>
    </div>
  );
}

function StaticField({ label, value }) {
  const displayValue = value === undefined || value === null || value === "" ? "Không có " : value;
  return (
    <label className="static-input">
      <span>{label}</span>
      <div className="static-input-box">{displayValue}</div>
    </label>
  );
}

function StaticTextarea({ label, value, rows = 5 }) {
  const displayValue = value === undefined || value === null || value === "" ? "Không có " : value;
  return (
    <label className="static-textarea">
      <span>{label}</span>
      <div className="static-textarea-box" style={{ minHeight: `${rows * 24 + 40}px` }}>{displayValue}</div>
    </label>
  );
}

function FunnelStep({ label, value }) {
  return (
    <div className="funnel-step">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function BarRow({ label, value, max }) {
  const width = `${Math.max(12, (value / Math.max(max, 1)) * 100)}%`;
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

export function AuthRoutePage(props) {
  return (
    <div className="auth-route-shell">
      <div className="auth-route-backdrop" />
      <div className="auth-route-content">
        <button className="ghost-btn auth-back-btn" type="button" onClick={props.closeAuthRoute}>
          Back to workspace
        </button>
        <AuthPanel {...props} />
      </div>
    </div>
  );
}

function AuthPanel({
  authMode,
  loginForm,
  setLoginForm,
  loginErrors,
  registerForm,
  setRegisterForm,
  registerErrors,
  handleLoginSubmit,
  handleRegisterSubmit,
  loading,
  statusMessage,
  openAuthRoute,
  closeAuthRoute,
}) {
  return (
    <section className="auth-embed">
      <div className="auth-brand panel auth-brand-embedded">
        <p className="eyebrow">Account Access</p>
        <h1>{authMode === "login" ? "Đăng nhập vào JobTrust" : "Tạo tài khoản mới"}</h1>
        <p>Bạn có thể quay lại workspace bất kỳ lúc nào. Sau khi đăng nhập, hệ thống sẽ mở khóa dữ liệu cá nhân, statistics và tracking.</p>
      </div>

      <div className="auth-panel">
        <div className="auth-tabs">
          <button
            className={authMode === "login" ? "tab-btn active" : "tab-btn"}
            onClick={() => openAuthRoute("login")}
          >
            Login
          </button>
          <button
            className={authMode === "register" ? "tab-btn active" : "tab-btn"}
            onClick={() => openAuthRoute("register")}
          >
            Register
          </button>
        </div>

        {authMode === "login" ? (
          <form className="auth-form" onSubmit={handleLoginSubmit} noValidate>
            <h2>Đăng nhập</h2>
            <Field
              label="Email"
              type="email"
              value={loginForm.email}
              onChange={(value) => setLoginForm({ ...loginForm, email: value })}
              error={loginErrors.email}
              autoComplete="email"
              maxLength={120}
              inputMode="email"
              required
            />
            <Field
              label="Password"
              type="password"
              value={loginForm.password}
              onChange={(value) => setLoginForm({ ...loginForm, password: value })}
              error={loginErrors.password}
              autoComplete="current-password"
              minLength={6}
              maxLength={72}
              required
            />
            {loginErrors.general && <p className="error-banner">{loginErrors.general}</p>}
            <div className="auth-actions">
              <button className="primary-btn auth-submit-btn" type="submit" disabled={loading}>
                Login
              </button>
              <button className="ghost-btn auth-secondary-btn" type="button" onClick={closeAuthRoute}>
                Close
              </button>
            </div>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegisterSubmit} noValidate>
            <h2>Tạo tài khoản</h2>
            <Field
              label="Name"
              value={registerForm.name}
              onChange={(value) => setRegisterForm({ ...registerForm, name: value })}
              error={registerErrors.name}
              autoComplete="name"
              maxLength={80}
              required
            />
            <Field
              label="Email"
              type="email"
              value={registerForm.email}
              onChange={(value) => setRegisterForm({ ...registerForm, email: value })}
              error={registerErrors.email}
              autoComplete="email"
              maxLength={120}
              inputMode="email"
              required
            />
            <Field
              label="Password"
              type="password"
              value={registerForm.password}
              onChange={(value) => setRegisterForm({ ...registerForm, password: value })}
              error={registerErrors.password}
              autoComplete="new-password"
              minLength={6}
              maxLength={72}
              required
            />
            <Field
              label="Confirm password"
              type="password"
              value={registerForm.confirmPassword}
              onChange={(value) => setRegisterForm({ ...registerForm, confirmPassword: value })}
              error={registerErrors.confirmPassword}
              autoComplete="new-password"
              minLength={6}
              maxLength={72}
              required
            />
            {registerErrors.general && <p className="error-banner">{registerErrors.general}</p>}
            <div className="auth-actions">
              <button className="primary-btn auth-submit-btn" type="submit" disabled={loading}>
                Register
              </button>
              <button className="ghost-btn auth-secondary-btn" type="button" onClick={closeAuthRoute}>
                Close
              </button>
            </div>
          </form>
        )}

        <div className="status-chip">{statusMessage}</div>
      </div>
    </section>
  );
}

export function DashboardPanel({ overview, stats, token, onOpenRecommendations, buildRiskPercent }) {
  if (!overview) {
    return <section className="panel">Đang tải dashboard...</section>;
  }

  return (
    <section className="panel-grid">
      <div className="stats-grid">
        <StatCard title="Total jobs" value={overview.summary?.totalJobs || 0} accent="blue" />
        <StatCard title="% risky jobs" value={buildRiskPercent(overview.summary)} accent="red" />
      </div>

      <div className="panel-grid double">
        <div className="panel">
          <h3>Risk distribution</h3>
          <div className="bar-list">
            {(overview.charts?.riskDistribution || []).map((item) => (
              <BarRow key={item.label} label={item.label} value={item.value} max={overview.summary?.totalJobs || 1} />
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Top companies</h3>
          <div className="metric-list">
            {(overview.charts?.topCompanies || []).map((item) => (
              <div key={item.name} className="metric-row">
                <span>{item.name}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel-grid double">
        <div className="panel">
          <h3>Warning signals</h3>
          <div className="metric-list">
            {(overview.charts?.topReasons || []).length === 0 && <p className="muted">Chưa có dữ liệu cảnh báo nổi bật.</p>}
            {(overview.charts?.topReasons || []).map((item) => (
              <div key={item.reason} className="metric-row">
                <span>{item.reason}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Personal snapshot</h3>
          {token ? (
            <div className="funnel">
              <FunnelStep label="Saved" value={stats?.savedCount || 0} />
              <FunnelStep label="Applied" value={stats?.total || 0} />
              <FunnelStep label="Success rate" value={`${stats?.successRate || 0}%`} />
              <button className="primary-btn" onClick={onOpenRecommendations}>Open analysis workspace</button>
            </div>
          ) : (
            <p className="muted">Đăng nhập để xem dashboard cá nhân và dữ liệu tracking của bạn.</p>
          )}
        </div>
      </div>
    </section>
  );
}

export function AnalysisWorkspace({
  mode,
  setMode,
  analysisForm,
  setAnalysisForm,
  analysisFormValidation,
  onAnalyzeSingle,
  analysisRequest,
  batchText,
  setBatchText,
  batchAnalysis,
  buildAnalysisSummary,
  onAnalyzeBatch,
  jobs,
  total,
  query,
  page,
  totalPages,
  setQuery,
  onSearch,
  onPrevious,
  onNext,
  onPickJob,
  onOpenJob,
  onSaveJob,
  onApplyJob,
}) {
  const singleAnalyzePending = analysisRequest.pending && analysisRequest.context === "single";
  const batchAnalyzePending = analysisRequest.pending && analysisRequest.context === "batch";
  const singleAnalyzeError = !analysisRequest.pending && analysisRequest.context === "single" ? analysisRequest.error : "";
  const batchAnalyzeError = !analysisRequest.pending && analysisRequest.context === "batch" ? analysisRequest.error : "";
  const singleAnalyzeMessage = !singleAnalyzeError && analysisRequest.context === "single" ? analysisRequest.message : "";
  const batchAnalyzeMessage = !batchAnalyzeError && analysisRequest.context === "batch" ? analysisRequest.message : "";

  return (
    <section className="panel-grid">
      <div className="panel panel-stack">
        <div className="section-heading">
          <div>
            <h3>Phân tích tin tuyển dụng</h3>
            <p className="muted">Phân tích 1 tin để xem chi tiết, hoặc dán nhiều tin để hệ thống phân tích hàng loạt.</p>
          </div>
          <div className="segmented-switch">
            <button className={mode === "single" ? "tab-btn active" : "tab-btn"} onClick={() => setMode("single")} type="button">
              Phân tích 1 tin
            </button>
            <button className={mode === "batch" ? "tab-btn active" : "tab-btn"} onClick={() => setMode("batch")} type="button">
              Phân tích nhiều tin
            </button>
          </div>
        </div>
      </div>

      {mode === "single" ? (
        <section className="panel-grid double analysis-layout">
          <div className="panel panel-stack analysis-form-panel">
            {singleAnalyzeError && <div className="error-banner">{singleAnalyzeError}</div>}
            {singleAnalyzeMessage && <div className={singleAnalyzePending ? "status-banner pending" : "status-banner success"}>{singleAnalyzeMessage}</div>}

            {analysisFormValidation.warnings.length > 0 && (
              <div className="info-banner">
                <strong>💡 Gợi ý cải thiện phân tích:</strong>
                <ul style={{ marginTop: "8px", paddingLeft: "20px" }}>
                  {analysisFormValidation.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="detail-grid">
              <Field
                label="Job title *"
                value={analysisForm.title}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, title: value }))}
                error={analysisFormValidation.errors.title}
                maxLength={160}
              />
              <Field
                label="Tên công ty"
                value={analysisForm.companyName}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, companyName: value }))}
                error={analysisFormValidation.errors.companyName}
                maxLength={160}
              />
              <Field
                label="Mức lương"
                value={analysisForm.salary}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, salary: value }))}
                error={analysisFormValidation.errors.salary}
                maxLength={120}
              />
              <Field
                label="Số lượng ứng viên"
                type="text"
                value={analysisForm.candidates}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, candidates: value }))}
                error={analysisFormValidation.errors.candidates}
                maxLength={40}
                inputMode="numeric"
              />
            </div>

            <label>
              <span>Mô tả *</span>
              <small style={{ color: analysisFormValidation.errors.description ? "#d32f2f" : "#999" }}>
                {analysisFormValidation.errors.description ? `❌ ${analysisFormValidation.errors.description}` : "Nhập ít nhất 20 ký tự"}
              </small>
              <textarea
                rows="6"
                value={analysisForm.description}
                onChange={(event) => setAnalysisForm((current) => ({ ...current, description: event.target.value.slice(0, 2500) }))}
                maxLength={2500}
                className={analysisFormValidation.errors.description ? "textarea-error" : ""}
              />
            </label>

            <label>
              <span>Yêu cầu *</span>
              <small style={{ color: analysisFormValidation.errors.requirements ? "#d32f2f" : "#999" }}>
                {analysisFormValidation.errors.requirements ? `❌ ${analysisFormValidation.errors.requirements}` : "Nhập ít nhất 10 ký tự"}
              </small>
              <textarea
                rows="4"
                value={analysisForm.requirements}
                onChange={(event) => setAnalysisForm((current) => ({ ...current, requirements: event.target.value.slice(0, 1800) }))}
                maxLength={1800}
                className={analysisFormValidation.errors.requirements ? "textarea-error" : ""}
              />
            </label>

            <label>
              <span>Phúc lợi</span>
              <textarea
                rows="3"
                value={analysisForm.benefits}
                onChange={(event) => setAnalysisForm((current) => ({ ...current, benefits: event.target.value.slice(0, 1000) }))}
                maxLength={1000}
              />
            </label>

            <div className="detail-grid">
              <Field
                label="Loại công việc"
                value={analysisForm.jobType}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, jobType: value }))}
                maxLength={80}
              />
              <Field
                label="Vị trí ứng tuyển"
                value={analysisForm.careerLevel}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, careerLevel: value }))}
                maxLength={80}
              />
              <Field
                label="Kinh nghiệm yêu cầu"
                value={analysisForm.experience}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, experience: value }))}
                maxLength={80}
              />
            </div>

            <div className="card-actions">
              <button className="primary-btn" type="button" onClick={onAnalyzeSingle} disabled={singleAnalyzePending}>
                {singleAnalyzePending ? "Đang phân tích..." : "Phân tích tin này"}
              </button>
              <button className="secondary-btn" type="button" onClick={() => onSaveJob(analysisForm)}>
                Save job
              </button>
              <button className="ghost-btn" type="button" onClick={() => onApplyJob(analysisForm)}>
                Add application
              </button>
            </div>
          </div>

          <div className="panel panel-stack">
            <div className="section-heading">
              <div>
                <h3>Chọn nhanh từ dữ liệu hiện có</h3>
                <p className="muted">Giữ lại trải nghiệm cũ bằng cách chọn một tin từ danh sách rồi phân tích tiếp.</p>
              </div>
              <div className="metric-chip">{total} jobs</div>
            </div>
            <form className="filter-row" onSubmit={(event) => { event.preventDefault(); onSearch(); }}>
              <input value={query} onChange={(event) => setQuery(event.target.value.slice(0, 120))} placeholder="Tìm theo title hoặc company..." maxLength={120} />
              <button className="primary-btn" type="submit">Tìm</button>
            </form>
            <div className="quick-job-list">
              {jobs.map((job) => (
                <article key={job.id} className="quick-job-card">
                  <div className="quick-job-card-content">
                    <strong>{job.title}</strong>
                    <p className="muted">{job.companyName || "Unknown company"}</p>
                    <p className="muted">{job.location || "Toàn quốc"} • {job.salary || "Không có "}</p>
                  </div>
                  <div className="quick-job-actions">
                    <button className="secondary-btn" type="button" onClick={() => onPickJob(job)}>Đưa vào form</button>
                    <button className="ghost-btn" type="button" onClick={() => onOpenJob(job)}>Chi tiết</button>
                  </div>
                </article>
              ))}
            </div>
            <div className="pagination-strip">
              <button className="secondary-btn" onClick={onPrevious} disabled={page <= 1} type="button">Previous</button>
              <strong>Page {page} / {totalPages || 1}</strong>
              <button className="secondary-btn" onClick={onNext} disabled={!totalPages || page >= totalPages} type="button">Next</button>
            </div>
          </div>
        </section>
      ) : (
        <section className="panel-grid double">
          <div className="panel panel-stack">
            <div>
              <h3>Dán nhiều tin tuyển dụng</h3>
              <p className="muted">Mỗi tin cách nhau bằng một dòng trống. Backend sẽ tự parse rồi phân tích hàng loạt.</p>
            </div>
            <div className="result-box batch-input-note">
              <strong>Lưu ý nhập liệu</strong>
              <p>Mỗi tin tuyển dụng cần cách nhau bằng một dòng trống để hệ thống tách đúng từng tin.</p>
              <p>Hãy nhập hoặc dán theo dạng: tin 1, xuống 2 dòng, rồi đến tin 2.</p>
            </div>
            {batchAnalyzeError && <div className="error-banner">{batchAnalyzeError}</div>}
            {batchAnalyzeMessage && <div className={batchAnalyzePending ? "status-banner pending" : "status-banner success"}>{batchAnalyzeMessage}</div>}
            <textarea
              className="batch-input-textarea"
              rows="20"
              value={batchText}
              onChange={(event) => setBatchText(event.target.value.slice(0, 12000))}
              maxLength={12000}
              placeholder={"Tin 1...\n\nTin 2...\n\nTin 3..."}
            />
            <button className="primary-btn" type="button" onClick={onAnalyzeBatch} disabled={batchAnalyzePending}>
              {batchAnalyzePending ? "Đang phân tích..." : "Phân tích nhiều tin"}
            </button>
          </div>

          <div className="panel panel-stack">
            <h3>Kết quả batch</h3>
            {!batchAnalysis && <p className="muted">Chưa có kết quả. Bấm phân tích để xem danh sách đánh giá.</p>}
            {batchAnalysis && (
              <>
                <div className="summary-grid">
                  <StatCard title="Tổng tin" value={batchAnalysis.summary?.total || 0} accent="blue" />
                  <StatCard title="Tách được" value={batchAnalysis.summary?.parsedFromText || 0} accent="green" />
                </div>
                {(batchAnalysis.parsingNotes || []).length > 0 && (
                  <div className="result-box suspicious">
                    {(batchAnalysis.parsingNotes || []).map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                  </div>
                )}
                <div className="batch-result-list">
                  {(batchAnalysis.items || []).map((item, index) => (
                    <article key={`${item.job?.title || "job"}-${index}`} className="batch-result-card">
                      {(() => {
                        const summary = buildAnalysisSummary ? buildAnalysisSummary(item) : null;
                        return (
                          <>
                            <h4>{item.job?.title || "Untitled job"}</h4>
                            <p>{item.job?.companyName || "Unknown company"}</p>
                            <p className="muted">{item.job?.address || "Chưa có địa chỉ"} • {item.job?.salary || "Không có "}</p>
                            {summary && (
                              <div className="metric-list">
                                <div className="metric-row">
                                  <span>Risk score</span>
                                  <strong>{summary.riskScore}</strong>
                                </div>
                                <div className="metric-row">
                                  <span>Trust score</span>
                                  <strong>{summary.trustScore}</strong>
                                </div>
                                <div className="metric-row">
                                  <span>Mức độ</span>
                                  <strong>{summary.riskLevel}</strong>
                                </div>
                                <div className="metric-row">
                                  <span>Kết luận</span>
                                  <strong>{summary.decision}</strong>
                                </div>
                                <div className="metric-row">
                                  <span>Cảnh báo</span>
                                  <strong>{item.signals?.length || 0}</strong>
                                </div>
                              </div>
                            )}
                          </>
                        );
                      })()}
                      <div className="card-actions">
                        <button className="secondary-btn" type="button" onClick={() => onOpenJob(item.job, item)}>Chi tiết</button>
                        <button className="ghost-btn" type="button" onClick={() => onSaveJob(item.job)}>Save</button>
                        <button className="primary-btn" type="button" onClick={() => onApplyJob(item.job)}>Apply</button>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}
          </div>
        </section>
      )}
    </section>
  );
}

export function JobDetailPanel({
  job,
  analysis,
  viewMode = "analysis",
  analysisRequest,
  systemBlacklist,
  userBlacklist,
  onBack,
  onAnalyze,
  onSaveJob,
  onApplyJob,
  normalizeJobRecord,
  enrichAnalysisResult,
  buildAnalysisSummary,
}) {
  if (!job) {
    return <section className="panel">Hãy chọn một job từ Job List để xem chi tiết.</section>;
  }

  const normalizedJob = normalizeJobRecord(job);
  const analysisWithBlacklist = enrichAnalysisResult(analysis, normalizedJob, systemBlacklist, userBlacklist);
  const detailAnalyzePending = analysisRequest.pending && analysisRequest.context === "detail";
  const detailAnalyzeError = !analysisRequest.pending && analysisRequest.context === "detail" ? analysisRequest.error : "";
  const detailAnalyzeMessage = !detailAnalyzeError && analysisRequest.context === "detail" ? analysisRequest.message : "";
  const showAnalysisPanel =
    viewMode === "analysis" && Boolean(analysisWithBlacklist || detailAnalyzePending || detailAnalyzeError || detailAnalyzeMessage);
  const analysisSummary = analysisWithBlacklist ? buildAnalysisSummary(analysisWithBlacklist) : null;
  const layoutClassName = showAnalysisPanel ? "panel-grid double job-detail-layout" : "panel-grid job-detail-layout";
  const detailFields = [
    { label: "Tiêu đề công việc", value: normalizedJob.title, type: "field" },
    { label: "Tên công ty", value: normalizedJob.companyName, type: "field" },
    { label: "Mức lương", value: normalizedJob.salary, type: "field" },
    { label: "Địa chỉ", value: normalizedJob.address || normalizedJob.location, type: "field" },
    { label: "Email", value: normalizedJob.email, type: "field" },
    { label: "Số điện thoại", value: normalizedJob.phone, type: "field" },
    { label: "Mô tả", value: normalizedJob.description, type: "textarea", rows: 7 },
    { label: "Yêu cầu", value: normalizedJob.requirements, type: "textarea", rows: 5 },
    { label: "Phúc lợi", value: normalizedJob.benefits, type: "textarea", rows: 5 },
  ];
  const metaFields = [
    { label: "Loại công việc", value: normalizedJob.jobType },
    { label: "Số lượng tuyển", value: normalizedJob.candidates },
    { label: "Vị trí ứng tuyển", value: normalizedJob.careerLevel },
    { label: "Kinh nghiệm yêu cầu", value: normalizedJob.experience },
    { label: "Hạn nộp hồ sơ", value: normalizedJob.submissionDeadline },
  ];

  return (
    <section className={layoutClassName}>
      <div className="panel panel-stack">
        <div className="section-heading">
          <div>
            <h3>Chi tiết công việc</h3>
            <p className="muted">Xem thông tin công việc và chạy phân tích độ uy tín trực tiếp.</p>
          </div>
          <button className="secondary-btn" onClick={onBack}>Quay lại danh sách</button>
        </div>
        {detailAnalyzeError && <div className="error-banner">{detailAnalyzeError}</div>}
        {detailAnalyzeMessage && <div className={detailAnalyzePending ? "status-banner pending" : "status-banner success"}>{detailAnalyzeMessage}</div>}
        {viewMode === "form" ? (
          <>
            <div className="detail-grid">
              {detailFields.slice(0, 6).map((field) => (
                <StaticField key={field.label} label={field.label} value={field.value} />
              ))}
            </div>
            {detailFields.slice(6).map((field) => (
              <StaticTextarea key={field.label} label={field.label} value={field.value} rows={field.rows} />
            ))}
            <div className="detail-grid detail-grid-job">
              {metaFields.map((field) => (
                <DetailItem
                  key={field.label}
                  label={field.label}
                  value={field.value}
                  multiline={field.multiline}
                  longText={field.longText}
                />
              ))}
            </div>
            <div className="card-actions">
              <button className="secondary-btn" onClick={() => onSaveJob(job)}>Lưu</button>
              <button className="ghost-btn" onClick={() => onApplyJob(job)}>Ứng tuyển</button>
            </div>
          </>
        ) : (
          <>
            <div className="detail-grid detail-grid-job">
              {metaFields.concat(detailFields.map((field) => ({
                label: field.label,
                value: field.value,
                multiline: field.type === "textarea",
                longText: field.type === "textarea",
              }))).map((field) => (
                <DetailItem
                  key={field.label}
                  label={field.label}
                  value={field.value}
                  multiline={field.multiline}
                  longText={field.longText}
                />
              ))}
            </div>
            <div className="card-actions">
              <button className="secondary-btn" onClick={() => onSaveJob(job)}>Lưu</button>
              <button className="ghost-btn" onClick={() => onApplyJob(job)}>Ứng tuyển</button>
              <button className="primary-btn" onClick={onAnalyze} disabled={detailAnalyzePending}>
                {detailAnalyzePending ? "Đang phân tích..." : "Phân tích"}
              </button>
            </div>
          </>
        )}
      </div>

      {showAnalysisPanel && (
        <div className="panel panel-stack">
          <h3>Kết quả phân tích</h3>
          {!analysisWithBlacklist && <p className="muted">Chưa có kết quả phân tích. Bấm Phân tích nếu bạn muốn xem cảnh báo nội dung và đối chiếu blacklist.</p>}
          {analysisWithBlacklist && (
            <>
              <div className="analysis-score-grid">
                <div className="score-card risk">
                  <span>Điểm rủi ro</span>
                  <strong>{analysisSummary.riskScore}</strong>
                </div>
                <div className="score-card trust">
                  <span>Điểm tin cậy</span>
                  <strong>{analysisSummary.trustScore}</strong>
                </div>
              </div>
              <div className="metric-list">
                <div className="metric-row">
                  <span>Mức độ nguy hiểm</span>
                  <strong>{analysisSummary.riskLevel}</strong>
                </div>
                <div className="metric-row">
                  <span>Kết luận</span>
                  <strong>{analysisSummary.decision}</strong>
                </div>
                <div className="metric-row">
                  <span>Blacklist chung</span>
                  <strong>{analysisWithBlacklist.blacklist?.system?.hasMatch ? "Trùng" : "An toàn"}</strong>
                </div>
                <div className="metric-row">
                  <span>Blacklist cá nhân</span>
                  <strong>{analysisWithBlacklist.blacklist?.personal?.hasMatch ? "Trùng" : "An toàn"}</strong>
                </div>
                <div className="metric-row">
                  <span>Đối chiếu tổng</span>
                  <strong>{analysisWithBlacklist.blacklist?.hasMatch ? "Trùng" : "An toàn"}</strong>
                </div>
                <div className="metric-row">
                  <span>Số cảnh báo</span>
                  <strong>{analysisWithBlacklist.signals?.length || 0}</strong>
                </div>
              </div>
              <div className="detail-block">
                <h4>Tín hiệu cảnh báo</h4>
                {(analysisWithBlacklist.signals || []).length === 0 && <p className="muted">Chưa ghi nhận tín hiệu rủi ro rõ ràng.</p>}
                <ul>
                  {(analysisWithBlacklist.signals || []).map((signal) => (
                    <li key={signal}>{signal}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

export function SavedJobsPanel({ savedJobs, onApply, onDelete, onNoteSave }) {
  return (
    <section className="panel-grid">
      <div className="section-heading">
        <div>
          <h3>Saved Jobs</h3>
        </div>
        <div className="metric-chip">{savedJobs.length} jobs</div>
      </div>

      {savedJobs.length === 0 ? (
        <div className="panel empty-panel">Chưa có saved job nào trong tài khoản này.</div>
      ) : (
        <div className="saved-grid">
          {savedJobs.map((item) => (
            <SavedJobCard key={item.id} item={item} onApply={onApply} onDelete={onDelete} onNoteSave={onNoteSave} />
          ))}
        </div>
      )}
    </section>
  );
}

function SavedJobCard({ item, onApply, onDelete, onNoteSave }) {
  const [note, setNote] = useState(item.note || "");

  useEffect(() => {
    setNote(item.note || "");
  }, [item.note]);

  return (
    <article className="panel saved-card">
      <h4>{item.job?.title || "Untitled job"}</h4>
      <p>{item.job?.companyName || "Unknown company"}</p>
      <p className="muted">{item.job?.location || "No location"} • {item.job?.salary || "No salary"}</p>
      <label>
        <span>Note</span>
        <textarea rows="4" value={note} onChange={(event) => setNote(event.target.value.slice(0, 500))} maxLength={500} />
      </label>
      <div className="card-actions">
        <button className="secondary-btn" onClick={() => onNoteSave(item.id, note)}>
          Save note
        </button>
        <button className="primary-btn" onClick={() => onApply({ ...item, note })}>
          Apply
        </button>
        <button className="ghost-btn" onClick={() => onDelete(item.id)}>
          Remove
        </button>
      </div>
    </article>
  );
}

export function ApplicationsPanel({ columns, groups, onDropStatus, onDelete, onOpenJob }) {
  return (
    <section className="panel-grid">
      <div className="section-heading">
        <div>
          <h3>Applications Kanban</h3>
        </div>
      </div>
      <div className="kanban-board">
        {columns.map((column) => (
          <div
            key={column.id}
            className="kanban-column"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => onDropStatus(event, column.id)}
          >
            <div className="kanban-header">
              <strong>{column.label}</strong>
              <span>{groups[column.id]?.length || 0}</span>
            </div>
            <div className="kanban-list">
              {(groups[column.id] || []).map((application) => (
                <ApplicationCard key={application.id} item={application} onDelete={onDelete} onOpenJob={onOpenJob} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ApplicationCard({ item, onDelete, onOpenJob }) {
  return (
    <article
      className="application-card compact"
      draggable
      onDragStart={(event) => event.dataTransfer.setData("applicationId", String(item.id))}
      onClick={() => onOpenJob(item)}
    >
      <h4>{item.job?.title || "Untitled job"}</h4>
      <p className="muted">{item.job?.companyName || "Unknown company"}</p>
      <div className="card-actions">
        <button className="secondary-btn" type="button" onClick={(event) => { event.stopPropagation(); onOpenJob(item); }}>
          Detail
        </button>
        <button className="ghost-btn" type="button" onClick={(event) => { event.stopPropagation(); onDelete(item.id); }}>
          Delete
        </button>
      </div>
    </article>
  );
}

export function BlacklistPanel({
  token,
  blacklist,
  checkForm,
  setCheckForm,
  checkResult,
  onCheck,
  userBlacklist,
  userBlacklistForm,
  setUserBlacklistForm,
  userBlacklistMatches,
  onAddUserBlacklist,
  onRemoveUserBlacklist,
}) {
  return (
    <section className={token ? "panel-grid double" : "panel-grid"}>
      <div className="panel panel-stack">
        <div>
          <h3>Check blacklist hệ thống</h3>
          <p className="muted">Kiểm tra nhanh bằng job title và tên công ty. Dữ liệu hệ thống hiện tập trung nhiều vào blacklist công ty.</p>
        </div>
        <div className="summary-grid">
          <StatCard title="Companies" value={blacklist.companies?.length || 0} accent="amber" />
          <StatCard title="Emails" value={blacklist.emails?.length || 0} accent="blue" />
          <StatCard title="Phones" value={blacklist.phones?.length || 0} accent="red" />
        </div>
        <div className="detail-block">
          <h4>Check input</h4>
          <label>
            <span>Job title</span>
            <input value={checkForm.title} onChange={(event) => setCheckForm({ ...checkForm, title: event.target.value.slice(0, 120) })} maxLength={120} />
          </label>
          <label>
            <span>Tên công ty</span>
            <input value={checkForm.companyName} onChange={(event) => setCheckForm({ ...checkForm, companyName: event.target.value.slice(0, 160) })} maxLength={160} />
          </label>
          <button className="secondary-btn" onClick={onCheck} type="button">
            Check
          </button>
        </div>

        <div className="detail-block">
          <h4>Kết quả hệ thống</h4>
          {!checkResult && <p className="muted">Chưa có kết quả kiểm tra.</p>}
          {checkResult && (
            <div className={checkResult.hasMatch ? "result-box suspicious" : "result-box safe"}>
              <strong>{checkResult.hasMatch ? "Suspicious" : "Safe"}</strong>
              <p>
                {checkResult.hasMatch
                  ? `Match: ${(checkResult.details || []).join(", ")}`
                  : "Không tìm thấy từ khóa hoặc thực thể blacklist trùng khớp."}
              </p>
            </div>
          )}
        </div>
      </div>

      {token && (
        <div className="panel panel-stack">
          <div>
            <h3>Blacklist riêng của user</h3>
            <p className="muted">Mỗi tài khoản sẽ có danh sách công ty và job title riêng. User khác sẽ không thấy dữ liệu này.</p>
          </div>
          <div className="detail-grid">
            <Field
              label="Job title"
              value={userBlacklistForm.title}
              onChange={(value) => setUserBlacklistForm((current) => ({ ...current, title: value }))}
              maxLength={120}
            />
            <Field
              label="Tên công ty"
              value={userBlacklistForm.companyName}
              onChange={(value) => setUserBlacklistForm((current) => ({ ...current, companyName: value }))}
              maxLength={160}
            />
          </div>
          <button className="primary-btn" type="button" onClick={onAddUserBlacklist}>
            Lưu blacklist riêng
          </button>

          <div className="detail-block">
            <h4>Match với input hiện tại</h4>
            {userBlacklistMatches.length === 0 ? (
              <p className="muted">Không có mục nào trong blacklist riêng của bạn khớp với title/company đang nhập.</p>
            ) : (
              <div className="vertical-list">
                {userBlacklistMatches.map((item) => (
                  <article key={item.id} className="user-blacklist-item warning">
                    <div className="user-blacklist-meta">
                      <div className="mini-field">
                        <span>Job title</span>
                        <strong>{item.title || "Chưa nhập"}</strong>
                      </div>
                      <div className="mini-field">
                        <span>Tên công ty</span>
                        <strong>{item.companyName || "Chưa nhập"}</strong>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="detail-block">
            <h4>Danh sách blacklist riêng</h4>
            {userBlacklist.length === 0 ? (
              <p className="muted">Tài khoản này chưa lưu blacklist riêng nào.</p>
            ) : (
              <div className="user-blacklist-list">
                {userBlacklist.map((item) => (
                  <article key={item.id} className="user-blacklist-item">
                    <div className="user-blacklist-meta">
                      <div className="mini-field">
                        <span>Job title</span>
                        <strong>{item.title || "Chưa nhập"}</strong>
                      </div>
                      <div className="mini-field">
                        <span>Tên công ty</span>
                        <strong>{item.companyName || "Chưa nhập"}</strong>
                      </div>
                    </div>
                    <button className="ghost-btn" type="button" onClick={() => onRemoveUserBlacklist(item.id)}>
                      Xóa
                    </button>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

export function StatisticsPanel({ stats, token, findCount }) {
  if (!token) {
    return (
      <section className="panel panel-stack">
        <div>
          <h3>Thống kê cá nhân</h3>
          <p className="muted">Trang này chỉ hiển thị dữ liệu saved jobs, applications và funnel của riêng tài khoản đang đăng nhập.</p>
        </div>
        <div className="result-box safe">
          <strong>Chưa đăng nhập</strong>
          <p>Hãy đăng nhập để xem thống kê cá nhân của bạn.</p>
        </div>
      </section>
    );
  }

  if (!stats) {
    return <section className="panel">Chưa có thống kê cá nhân để hiển thị.</section>;
  }

  const interviewCount = findCount(stats.statusDistribution, "interviewing");
  const offerCount = findCount(stats.statusDistribution, "offered");
  const total = stats.total || 0;
  const applyToInterview = total ? Math.round((interviewCount / total) * 100) : 0;
  const interviewToOffer = interviewCount ? Math.round((offerCount / interviewCount) * 100) : 0;

  return (
    <section className="panel-grid">
      <div className="stats-grid">
        <StatCard title="Applied jobs" value={stats.total} accent="blue" />
        <StatCard title="Saved jobs" value={stats.savedCount} accent="amber" />
        <StatCard title="Interviewing" value={interviewCount} accent="green" />
        <StatCard title="Success rate" value={`${stats.successRate}%`} accent="red" />
      </div>

      <div className="panel">
        <h3>Status distribution</h3>
        <div className="bar-list">
          {(stats.statusDistribution || []).map((item) => (
            <BarRow key={item.status} label={item.label} value={item.count} max={stats.total || 1} />
          ))}
        </div>
      </div>

      <div className="panel-grid double">
        <div className="panel">
          <h3>Funnel</h3>
          <div className="funnel">
            <FunnelStep label="Saved" value={stats.savedCount} />
            <FunnelStep label="Applied" value={stats.total} />
            <FunnelStep label="Interview" value={interviewCount} />
            <FunnelStep label="Offer" value={offerCount} />
          </div>
        </div>

        <div className="panel">
          <h3>Metrics</h3>
          <div className="metric-list">
            <div className="metric-row">
              <span>Apply → Interview</span>
              <strong>{applyToInterview}%</strong>
            </div>
            <div className="metric-row">
              <span>Interview → Offer</span>
              <strong>{interviewToOffer}%</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Monthly applications</h3>
        <div className="bar-list">
          {(stats.monthlyApplications || []).length === 0 && <p className="muted">Chưa có dữ liệu theo tháng.</p>}
          {(stats.monthlyApplications || []).map((item) => (
            <BarRow
              key={item.month}
              label={item.month}
              value={item.count}
              max={Math.max(...stats.monthlyApplications.map((monthItem) => monthItem.count), 1)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export function ProfilePanel({
  preferences,
  keywordInput,
  setKeywordInput,
  addKeywordTag,
  removeKeywordTag,
  toggleJobType,
  setPreferences,
  errors,
  onSave,
  jobTypeOptions,
}) {
  return (
    <section className="panel-grid double">
      <div className="panel panel-stack">
        <div>
          <h3>Profile & Preferences</h3>
          <p className="muted">Tên, keywords, job types và preferred risk sẽ được lưu vào backend khi đã đăng nhập; guest mode vẫn giữ local.</p>
        </div>

        <label>
          <span>Name</span>
          <input
            value={preferences.name}
            onChange={(event) => setPreferences((current) => ({ ...current, name: event.target.value.slice(0, 80) }))}
            className={errors.name ? "input-error" : ""}
            maxLength={80}
          />
          {errors.name && <small className="error-text">{errors.name}</small>}
        </label>

        <label>
          <span>Email</span>
          <input value={preferences.email} disabled />
        </label>

        <div className="tag-editor">
          <label>
            <span>Keywords</span>
            <div className="tag-input-wrap">
              <input
                value={keywordInput}
                onChange={(event) => setKeywordInput(event.target.value.slice(0, 32))}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addKeywordTag();
                  }
                }}
                placeholder="Nhập keyword rồi bấm Enter"
                maxLength={32}
              />
              <button className="secondary-btn" type="button" onClick={addKeywordTag}>
                Add
              </button>
            </div>
          </label>
          <div className="tag-list">
            {preferences.keywords.map((keyword) => (
              <button key={keyword} className="tag-pill" onClick={() => removeKeywordTag(keyword)}>
                {keyword} ×
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="field-label">Job types</span>
          <div className="multi-select-grid">
            {jobTypeOptions.map((jobType) => {
              const active = preferences.jobTypes.includes(jobType);
              return (
                <button
                  key={jobType}
                  className={active ? "choice-chip active" : "choice-chip"}
                  type="button"
                  onClick={() => toggleJobType(jobType)}
                >
                  {jobType}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <span className="field-label">Preferred risk</span>
          <div className="multi-select-grid">
            {["LOW", "MEDIUM", "HIGH"].map((level) => {
              const active = preferences.preferredRisk.includes(level);
              return (
                <button
                  key={level}
                  className={active ? "choice-chip active" : "choice-chip"}
                  type="button"
                  onClick={() => setPreferences((current) => {
                    const exists = current.preferredRisk.includes(level);
                    const nextRisk = exists
                      ? current.preferredRisk.filter((item) => item !== level)
                      : [...current.preferredRisk, level];
                    return {
                      ...current,
                      preferredRisk: nextRisk.length ? nextRisk : ["LOW", "MEDIUM"],
                    };
                  })}
                >
                  {level}
                </button>
              );
            })}
          </div>
        </div>

        {errors.general && <p className="error-banner">{errors.general}</p>}
        <button className="primary-btn" onClick={onSave}>
          Save changes
        </button>
      </div>

      <div className="panel panel-stack">
        <h3>Preference summary</h3>
        <div className="summary-card">
          <strong>{preferences.name || "Chưa có tên"}</strong>
          <p>{preferences.email || "Chưa có email"}</p>
        </div>
        <div>
          <span className="field-label">Keywords đang chọn</span>
          <div className="tag-list">
            {preferences.keywords.map((keyword) => (
              <span key={keyword} className="tag-pill static">
                {keyword}
              </span>
            ))}
          </div>
        </div>
        <div>
          <span className="field-label">Job types</span>
          <div className="tag-list">
            {preferences.jobTypes.map((jobType) => (
              <span key={jobType} className="tag-pill static">
                {jobType}
              </span>
            ))}
          </div>
        </div>
        <div>
          <span className="field-label">Preferred risk</span>
          <div className="tag-list">
            {preferences.preferredRisk.map((level) => (
              <span key={level} className="tag-pill static">
                {level}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
