import { useEffect, useMemo, useState } from "react";
import { api, authStorage } from "./api";
import { sampleBatchText, sampleJob } from "./mockData";

const APP_PREFERENCES_KEY = "jobtrust_profile_preferences";
const USER_BLACKLIST_STORAGE_KEY = "jobtrust_user_blacklist";
const JOB_TYPE_OPTIONS = ["Toàn thời gian", "Bán thời gian", "Remote", "Hybrid", "Thực tập", "Freelance"];
const KANBAN_COLUMNS = [
  { id: "saved", label: "Saved" },
  { id: "applied", label: "Applied" },
  { id: "interviewing", label: "Interviewing" },
  { id: "offered", label: "Offered" },
  { id: "rejected", label: "Rejected" },
];
const STATUS_OPTIONS = [
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offered", label: "Offered" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
];

const DEFAULT_PROFILE = {
  name: "",
  email: "",
  keywords: ["python", "data", "remote"],
  jobTypes: ["Toàn thời gian", "Remote"],
  preferredRisk: ["LOW", "MEDIUM"],
};

const DEFAULT_BLACKLIST_CHECK = {
  title: "",
  companyName: "",
};

const DEFAULT_ANALYSIS_FORM = {
  title: sampleJob.title,
  companyName: sampleJob.companyName,
  description: sampleJob.description,
  requirements: sampleJob.requirements,
  benefits: sampleJob.benefits,
  salary: sampleJob.salary,
  address: sampleJob.address,
  email: sampleJob.email,
  phone: sampleJob.phone,
  companySize: sampleJob.companySize,
  experience: sampleJob.experience,
  careerLevel: sampleJob.careerLevel,
  jobType: sampleJob.jobType,
};

const DEFAULT_USER_BLACKLIST_FORM = {
  title: "",
  companyName: "",
};

const menuSections = [
  {
    title: "Workspace",
    items: [
      { id: "dashboard", label: "Dashboard" },
      { id: "analysis", label: "Phân tích tin" },
      { id: "saved", label: "Saved Jobs" },
      { id: "applications", label: "Applications" },
      { id: "statistics", label: "Statistic" },
    ],
  },
  {
    title: "Safety & Account",
    items: [
      { id: "blacklist", label: "Blacklist" },
      { id: "profile", label: "Profile" },
    ],
  },
];

export default function App() {
  const [authMode, setAuthMode] = useState("login");
  const [activePage, setActivePage] = useState("analysis");
  const [routePath, setRoutePath] = useState(() => (typeof window === "undefined" ? "/" : window.location.pathname));
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [token, setToken] = useState(() => authStorage.getToken());
  const [user, setUser] = useState(null);
  const [preferences, setPreferences] = useState(() => loadPreferences());
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    name: "",
  });
  const [loginErrors, setLoginErrors] = useState({});
  const [registerErrors, setRegisterErrors] = useState({});
  const [profileErrors, setProfileErrors] = useState({});
  const [keywordInput, setKeywordInput] = useState("");
  const [savedJobs, setSavedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobQuery, setJobQuery] = useState("");
  const [jobRisk, setJobRisk] = useState("ALL");
  const [jobPage, setJobPage] = useState(1);
  const [jobTotalPages, setJobTotalPages] = useState(0);
  const [jobTotal, setJobTotal] = useState(0);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobAnalysis, setJobAnalysis] = useState(null);
  const [detailBackPage, setDetailBackPage] = useState("analysis");
  const [analysisMode, setAnalysisMode] = useState("single");
  const [analysisForm, setAnalysisForm] = useState(DEFAULT_ANALYSIS_FORM);
  const [batchText, setBatchText] = useState(sampleBatchText);
  const [batchAnalysis, setBatchAnalysis] = useState(null);
  const [stats, setStats] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [blacklist, setBlacklist] = useState({ companies: [], emails: [], phones: [] });
  const [blacklistCheckForm, setBlacklistCheckForm] = useState(DEFAULT_BLACKLIST_CHECK);
  const [blacklistCheckResult, setBlacklistCheckResult] = useState(null);
  const [userBlacklist, setUserBlacklist] = useState([]);
  const [userBlacklistLoadedKey, setUserBlacklistLoadedKey] = useState("");
  const [userBlacklistForm, setUserBlacklistForm] = useState(DEFAULT_USER_BLACKLIST_FORM);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Kết nối Flask backend để xem dữ liệu cá nhân.");
  const [successMessage, setSuccessMessage] = useState("");
  const isAuthRoute = routePath === "/login" || routePath === "/register";

  useEffect(() => {
    if (!successMessage) return;
    const timer = window.setTimeout(() => setSuccessMessage(""), 3200);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  useEffect(() => {
    function syncAuthRoute() {
      const path = window.location.pathname;
      setRoutePath(path);
      if (path === "/register") {
        setAuthMode("register");
      } else if (path === "/login") {
        setAuthMode("login");
      }
    }

    syncAuthRoute();
    window.addEventListener("popstate", syncAuthRoute);
    return () => window.removeEventListener("popstate", syncAuthRoute);
  }, []);

  useEffect(() => {
    authStorage.setToken(token);
  }, [token]);

  useEffect(() => {
    localStorage.setItem(APP_PREFERENCES_KEY, JSON.stringify(preferences));
  }, [preferences]);

  const userBlacklistOwnerKey = user?.id ? `id:${user.id}` : user?.email ? `email:${String(user.email).toLowerCase()}` : "";

  useEffect(() => {
    if (!userBlacklistOwnerKey) {
      setUserBlacklist([]);
      setUserBlacklistLoadedKey("");
      return;
    }
    setUserBlacklist(loadUserBlacklist(userBlacklistOwnerKey));
    setUserBlacklistLoadedKey(userBlacklistOwnerKey);
  }, [userBlacklistOwnerKey]);

  useEffect(() => {
    if (!userBlacklistOwnerKey || userBlacklistLoadedKey !== userBlacklistOwnerKey) return;
    saveUserBlacklist(userBlacklistOwnerKey, userBlacklist);
  }, [userBlacklistOwnerKey, userBlacklist, userBlacklistLoadedKey]);

  useEffect(() => {
    let ignore = false;

    async function bootstrap() {
      try {
        const blacklistData = await api.getBlacklist();
        if (ignore) return;
        setBlacklist(blacklistData);
      } catch (error) {
        if (!ignore) {
          setStatusMessage("Không tải được blacklist từ Flask backend.");
        }
      }

      try {
        const overviewData = await api.getOverview();
        if (ignore) return;
        setOverview(overviewData);
      } catch (error) {
        if (!ignore) {
          setStatusMessage("Không tải được dữ liệu tổng quan từ Flask backend.");
        }
      }

      try {
        const jobsData = await api.getJobs({ page: 1, pageSize: 9 });
        if (ignore) return;
        setJobs(jobsData.items || []);
        setJobTotal(jobsData.total || 0);
        setJobTotalPages(jobsData.totalPages || 0);
        setJobPage(jobsData.page || 1);
        setSelectedJob((current) => current || jobsData.items?.[0] || null);
        if (!analysisForm.title && jobsData.items?.[0]) {
          setAnalysisForm(mapJobToAnalysisForm(jobsData.items[0]));
        }
      } catch (error) {
        if (!ignore) {
          setStatusMessage("Không tải được danh sách job từ Flask backend.");
        }
      }

      if (!token) {
        return;
      }

      setLoading(true);
      try {
        const [profile, savedData, applicationsData, statsData, riskData] = await Promise.all([
          api.getProfile(),
          api.getSavedJobs(),
          api.getApplications({ pageSize: 100 }),
          api.getStatistics(),
          api.getRiskSummary(),
        ]);
        if (ignore) return;
        setUser(profile);
        setPreferences((current) => mergeProfilePreferences(current, profile));
        setSavedJobs(savedData.items || []);
        setApplications(applicationsData.items || []);
        setStats(statsData);
        setRiskSummary(riskData);
        setStatusMessage("Dữ liệu cá nhân đã đồng bộ từ backend Flask.");
      } catch (error) {
        if (ignore) return;
        if (error.status === 401) {
          handleLogout();
          setStatusMessage("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.");
        } else {
          setStatusMessage(error.message || "Không tải được dữ liệu cá nhân.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      ignore = true;
    };
  }, [token, analysisForm.title]);

  const applicationGroups = useMemo(() => {
    const groups = Object.fromEntries(KANBAN_COLUMNS.map((column) => [column.id, []]));
    applications.forEach((application) => {
      const key = groups[application.status] ? application.status : "rejected";
      groups[key].push(application);
    });
    return groups;
  }, [applications]);

  const userBlacklistMatches = useMemo(
    () => matchUserBlacklist(userBlacklist, blacklistCheckForm),
    [userBlacklist, blacklistCheckForm]
  );

  async function handleLoginSubmit(event) {
    event.preventDefault();
    const errors = validateLogin(loginForm);
    setLoginErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setLoading(true);
    try {
      const result = await api.login(loginForm);
      setToken(result.accessToken);
      setUser(result.user);
      setPreferences((current) => mergeProfilePreferences(current, result.user));
      setLoginForm({ email: "", password: "" });
      closeAuthRoute();
      setAccountMenuOpen(false);
      setActivePage("analysis");
      setStatusMessage("Đăng nhập thành công. JWT đã được lưu ở localStorage.");
      setSuccessMessage("Đăng nhập thành công.");
    } catch (error) {
      setLoginErrors({ general: error.message || "Đăng nhập thất bại." });
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterSubmit(event) {
    event.preventDefault();
    const errors = validateRegister(registerForm);
    setRegisterErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setLoading(true);
    try {
      await api.register({
        email: registerForm.email,
        password: registerForm.password,
        confirmPassword: registerForm.confirmPassword,
        name: registerForm.name,
      });
      setRegisterForm({ email: "", password: "", confirmPassword: "", name: "" });
      openAuthRoute("login");
      setStatusMessage("Đăng ký thành công. Bạn có thể đăng nhập ngay.");
      setSuccessMessage("Đăng ký thành công. Mời bạn đăng nhập.");
    } catch (error) {
      setRegisterErrors({ general: error.message || "Đăng ký thất bại." });
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    authStorage.clear();
    setToken("");
    setUser(null);
    setSavedJobs([]);
    setApplications([]);
    setStats(null);
    setRiskSummary(null);
    setActivePage("analysis");
    setStatusMessage("Bạn đang ở chế độ guest.");
    setAccountMenuOpen(false);
    closeAuthRoute();
  }

  async function refreshUserData(message) {
    if (!token) return;
    const [savedData, applicationsData, statsData, riskData] = await Promise.all([
      api.getSavedJobs(),
      api.getApplications({ pageSize: 100 }),
      api.getStatistics(),
      api.getRiskSummary(),
    ]);
    setSavedJobs(savedData.items || []);
    setApplications(applicationsData.items || []);
    setStats(statsData);
    setRiskSummary(riskData);
    if (message) {
      setStatusMessage(message);
    }
  }

  async function loadJobs(page = 1, query = jobQuery, risk = jobRisk) {
    try {
      const data = await api.getJobs({ page, pageSize: 9, query, risk });
      setJobs(data.items || []);
      setJobPage(data.page || 1);
      setJobTotal(data.total || 0);
      setJobTotalPages(data.totalPages || 0);
      if (data.items?.length) {
        setSelectedJob((current) => {
          if (current && data.items.some((item) => item.id === current.id)) {
            return current;
          }
          return data.items[0];
        });
      }
    } catch (error) {
      setStatusMessage(error.message || "Không tải được job list.");
    }
  }

  async function handleAnalyzeSelectedJob() {
    if (!selectedJob) return;
    try {
      const payload = mapJobToAnalysisPayload(selectedJob);
      const result = await api.analyzeJob(payload);
      setJobAnalysis(result);
      setActivePage("detail");
      setStatusMessage("Đã phân tích độ uy tín cho job đang chọn.");
    } catch (error) {
      setStatusMessage(error.message || "Không phân tích được job.");
    }
  }

  async function handleAnalyzeSingle() {
    try {
      const result = await api.analyzeJob(analysisForm);
      setSelectedJob(result.job || analysisForm);
      setJobAnalysis(result);
      setDetailBackPage("analysis");
      setActivePage("detail");
      setStatusMessage("Đã phân tích 1 tin tuyển dụng.");
    } catch (error) {
      setStatusMessage(error.message || "Không phân tích được tin tuyển dụng.");
    }
  }

  async function handleAnalyzeBatch() {
    try {
      const result = await api.batchAnalyze({ rawText: batchText });
      setBatchAnalysis(result);
      setAnalysisMode("batch");
      setStatusMessage("Đã phân tích nhiều tin tuyển dụng.");
    } catch (error) {
      setStatusMessage(error.message || "Không phân tích được danh sách tin.");
    }
  }

  async function handleSaveProfile() {
    const errors = validateProfile(preferences);
    setProfileErrors(errors);
    if (Object.keys(errors).length > 0) return;

    if (!token) {
      setStatusMessage("Đã lưu preferences trong localStorage. Đăng nhập nếu bạn muốn đồng bộ lên backend.");
      return;
    }

    setLoading(true);
    try {
      const updated = await api.updateProfile({
        name: preferences.name,
        preferences: {
          keywords: preferences.keywords,
          jobTypes: preferences.jobTypes,
          preferredRisk: preferences.preferredRisk,
        },
      });
      setUser(updated);
      setPreferences((current) => mergeProfilePreferences(current, updated));
      setStatusMessage("Đã lưu profile và preferences lên backend.");
    } catch (error) {
      setProfileErrors({ general: error.message || "Không lưu được profile." });
    } finally {
      setLoading(false);
    }
  }

  async function handleSavedNoteChange(id, note) {
    try {
      const updated = await api.updateSavedJob(id, { note });
      setSavedJobs((current) => current.map((item) => (item.id === id ? updated : item)));
      setStatusMessage("Đã cập nhật note cho saved job.");
    } catch (error) {
      setStatusMessage(error.message || "Không cập nhật được note.");
    }
  }

  async function handleSavedDelete(id) {
    try {
      await api.deleteSavedJob(id);
      await refreshUserData("Đã bỏ saved job.");
    } catch (error) {
      setStatusMessage(error.message || "Không xóa được saved job.");
    }
  }

  async function handleApplyFromSaved(item) {
    try {
      await api.applySavedJob(item.id, { note: item.note || "" });
      await refreshUserData("Đã chuyển job sang Applications.");
      setActivePage("applications");
    } catch (error) {
      setStatusMessage(error.message || "Không apply từ saved job được.");
    }
  }

  async function handleApplicationFieldChange(id, patch) {
    try {
      const updated = await api.updateApplication(id, patch);
      setApplications((current) => current.map((item) => (item.id === id ? updated : item)));
      setStatusMessage("Đã cập nhật application.");
    } catch (error) {
      setStatusMessage(error.message || "Không cập nhật được application.");
    }
  }

  async function handleDropStatus(event, status) {
    event.preventDefault();
    const appId = Number(event.dataTransfer.getData("applicationId"));
    if (!appId) return;
    await handleApplicationFieldChange(appId, { status });
  }

  async function handleDeleteApplication(id) {
    try {
      await api.deleteApplication(id);
      await refreshUserData("Đã xóa application.");
    } catch (error) {
      setStatusMessage(error.message || "Không xóa được application.");
    }
  }

  async function handleBlacklistCheck() {
    try {
      const result = await api.checkBlacklist({
        title: blacklistCheckForm.title,
        companyName: blacklistCheckForm.companyName,
      });
      setBlacklistCheckResult(result);
      setStatusMessage("Đã kiểm tra blacklist hệ thống cho tên công việc và công ty.");
    } catch (error) {
      setStatusMessage(error.message || "Không kiểm tra được blacklist.");
    }
  }

  function handleAddUserBlacklist() {
    const title = userBlacklistForm.title.trim();
    const companyName = userBlacklistForm.companyName.trim();
    if (!title && !companyName) {
      setStatusMessage("Nhập job title hoặc tên công ty để lưu blacklist riêng.");
      return;
    }

    const nextItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title,
      companyName,
    };
    const exists = userBlacklist.some(
      (item) =>
        item.title.toLowerCase() === title.toLowerCase() &&
        item.companyName.toLowerCase() === companyName.toLowerCase()
    );
    if (exists) {
      setStatusMessage("Mục blacklist riêng này đã tồn tại.");
      return;
    }

    setUserBlacklist((current) => [nextItem, ...current]);
    setUserBlacklistForm(DEFAULT_USER_BLACKLIST_FORM);
    setStatusMessage("Đã lưu vào blacklist riêng của bạn.");
  }

  function handleRemoveUserBlacklist(id) {
    setUserBlacklist((current) => current.filter((item) => item.id !== id));
    setStatusMessage("Đã xóa mục khỏi blacklist riêng.");
  }

  async function handleSaveJob(job) {
    if (!token) {
      setStatusMessage("Bạn đang ở guest mode. Hãy đăng nhập để lưu job.");
      openAuthRoute("login");
      return;
    }

    try {
      await api.createSavedJob(buildTrackingPayload(job));
      await refreshUserData("Đã lưu job vào Saved Jobs.");
      setActivePage("saved");
    } catch (error) {
      setStatusMessage(error.message || "Không lưu được job.");
    }
  }

  async function handleApplyJob(job) {
    if (!token) {
      setStatusMessage("Bạn đang ở guest mode. Hãy đăng nhập để theo dõi ứng tuyển.");
      openAuthRoute("login");
      return;
    }

    try {
      await api.createApplication(buildTrackingPayload(job));
      await refreshUserData("Đã thêm job vào Applications.");
      setActivePage("applications");
    } catch (error) {
      setStatusMessage(error.message || "Không tạo được application.");
    }
  }

  function openJobDetail(job, options = {}) {
    const { backPage = "analysis", analysis = null } = options;
    setSelectedJob(job);
    if (analysis) {
      setJobAnalysis(analysis);
    }
    setDetailBackPage(backPage);
    setActivePage("detail");
  }

  function handlePickQuickJob(job) {
    setAnalysisForm(mapJobToAnalysisForm(job));
    setSelectedJob(job);
    setStatusMessage("Đã đưa tin tuyển dụng vào form phân tích.");
  }

  function handleOpenApplicationJob(item) {
    openJobDetail(
      {
        ...item.job,
        id: item.jobId || item.job?.id || item.id,
        riskLevel: item.riskLevel,
        trustScore: item.trustScore,
      },
      { backPage: "applications" }
    );
  }

  function addKeywordTag() {
    const nextKeyword = keywordInput.trim();
    if (!nextKeyword) return;
    if (nextKeyword.length > 32 || preferences.keywords.length >= 12) {
      setProfileErrors((current) => ({ ...current, general: "Mỗi keyword tối đa 32 ký tự và không quá 12 keyword." }));
      return;
    }
    if (preferences.keywords.includes(nextKeyword)) {
      setKeywordInput("");
      return;
    }
    setPreferences((current) => ({
      ...current,
      keywords: [...current.keywords, nextKeyword],
    }));
    setProfileErrors((current) => ({ ...current, general: "" }));
    setKeywordInput("");
  }

  function removeKeywordTag(tag) {
    setPreferences((current) => ({
      ...current,
      keywords: current.keywords.filter((item) => item !== tag),
    }));
  }

  function toggleJobType(jobType) {
    setPreferences((current) => {
      const exists = current.jobTypes.includes(jobType);
      return {
        ...current,
        jobTypes: exists ? current.jobTypes.filter((item) => item !== jobType) : [...current.jobTypes, jobType],
      };
    });
  }

  function openAuthRoute(mode) {
    const path = mode === "register" ? "/register" : "/login";
    window.history.pushState({}, "", path);
    setRoutePath(path);
    setAuthMode(mode === "register" ? "register" : "login");
  }

  function closeAuthRoute() {
    window.history.pushState({}, "", "/");
    setRoutePath("/");
  }

  function navigateToPage(page) {
    if (page === "profile" && !token) {
      setStatusMessage("Vui lòng đăng nhập để vào trang profile.");
      openAuthRoute("login");
      return;
    }
    setActivePage(page);
  }

  if (isAuthRoute && !token) {
    return (
      <AuthRoutePage
        authMode={authMode}
        setAuthMode={setAuthMode}
        loginForm={loginForm}
        setLoginForm={setLoginForm}
        loginErrors={loginErrors}
        registerForm={registerForm}
        setRegisterForm={setRegisterForm}
        registerErrors={registerErrors}
        handleLoginSubmit={handleLoginSubmit}
        handleRegisterSubmit={handleRegisterSubmit}
        loading={loading}
        statusMessage={statusMessage}
        openAuthRoute={openAuthRoute}
        closeAuthRoute={closeAuthRoute}
      />
    );
  }

  return (
    <div className="app-shell">
      {successMessage && <div className="success-toast">{successMessage}</div>}
      <aside className="sidebar">
        <div className="sidebar-top">
          
          <div className="brand-lockup">
            <div className="brand-mark">JT</div>
         
          </div>
        </div>


        {menuSections.map((section) => (
          <div key={section.title}>
            <div className="menu-title">{section.title}</div>
            <nav className="menu">
              {section.items.map((item) => (
                <button
                  key={item.id}
                  className={activePage === item.id ? "menu-item active" : "menu-item"}
                  onClick={() => navigateToPage(item.id)}
                >
                  <span className="menu-label">{item.label}</span>
                  {item.id === "saved" && <span className="menu-badge">{savedJobs.length}</span>}
                  {item.id === "applications" && <span className="menu-badge">{applications.length}</span>}
                </button>
              ))}
            </nav>
          </div>
        ))}
      </aside>

      <main className="content">
        <section className="topbar">
          <div className="account-area">
            <button className="account-trigger" onClick={() => (token ? setAccountMenuOpen((current) => !current) : openAuthRoute("login"))}>
              <span className="avatar-badge">{buildAvatarLabel(token ? user?.name || preferences.name : "Guest")}</span>
              <span className="account-meta">
                <strong>{token ? user?.name || preferences.name || "Người dùng" : "Tài khoản"}</strong>
                <small>{token ? user?.email || preferences.email || "Đã đăng nhập" : "Đăng nhập / Đăng ký"}</small>
              </span>
            </button>

            {accountMenuOpen && token && (
              <div className="account-popover">
                <div className="account-menu">
                  <div className="account-summary">
                    <strong>{user?.name || preferences.name || "Người dùng"}</strong>
                    <span>{user?.email || preferences.email || "No email"}</span>
                  </div>
                  <button className="secondary-btn full-width" onClick={() => { navigateToPage("profile"); setAccountMenuOpen(false); }}>
                    Mở profile
                  </button>
                  <button className="ghost-btn full-width" onClick={() => { handleLogout(); setAccountMenuOpen(false); }}>
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {activePage === "dashboard" && <DashboardPanel overview={overview} stats={stats} token={Boolean(token)} onOpenRecommendations={() => setActivePage("analysis")} />}
        {activePage === "analysis" && (
          <AnalysisWorkspace
            mode={analysisMode}
            setMode={setAnalysisMode}
            analysisForm={analysisForm}
            setAnalysisForm={setAnalysisForm}
            onAnalyzeSingle={handleAnalyzeSingle}
            batchText={batchText}
            setBatchText={setBatchText}
            batchAnalysis={batchAnalysis}
            onAnalyzeBatch={handleAnalyzeBatch}
            jobs={jobs}
            total={jobTotal}
            query={jobQuery}
            risk={jobRisk}
            page={jobPage}
            totalPages={jobTotalPages}
            setQuery={setJobQuery}
            setRisk={setJobRisk}
            onSearch={() => loadJobs(1, jobQuery, jobRisk)}
            onPrevious={() => loadJobs(Math.max(1, jobPage - 1), jobQuery, jobRisk)}
            onNext={() => loadJobs(Math.min(jobTotalPages || 1, jobPage + 1), jobQuery, jobRisk)}
            onPickJob={handlePickQuickJob}
            onOpenJob={(job, analysis) => openJobDetail(job, { backPage: "analysis", analysis })}
            onSaveJob={handleSaveJob}
            onApplyJob={handleApplyJob}
          />
        )}
        {activePage === "saved" && (
          <SavedJobsPanel savedJobs={savedJobs} onApply={handleApplyFromSaved} onDelete={handleSavedDelete} onNoteSave={handleSavedNoteChange} />
        )}
        {activePage === "applications" && (
          <ApplicationsPanel
            columns={KANBAN_COLUMNS}
            groups={applicationGroups}
            onDropStatus={handleDropStatus}
            onDelete={handleDeleteApplication}
            onOpenJob={handleOpenApplicationJob}
          />
        )}
        {activePage === "blacklist" && (
          <BlacklistPanel
            token={Boolean(token)}
            blacklist={blacklist}
            checkForm={blacklistCheckForm}
            setCheckForm={setBlacklistCheckForm}
            checkResult={blacklistCheckResult}
            onCheck={handleBlacklistCheck}
            userBlacklist={userBlacklist}
            userBlacklistForm={userBlacklistForm}
            setUserBlacklistForm={setUserBlacklistForm}
            userBlacklistMatches={userBlacklistMatches}
            onAddUserBlacklist={handleAddUserBlacklist}
            onRemoveUserBlacklist={handleRemoveUserBlacklist}
          />
        )}
        {activePage === "statistics" && (
          <StatisticsPanel
            stats={stats}
            riskSummary={riskSummary}
            token={Boolean(token)}
            savedJobs={savedJobs}
            applications={applications}
            userBlacklist={userBlacklist}
          />
        )}
        {activePage === "profile" && (
          token ? (
            <ProfilePanel
              preferences={preferences}
              keywordInput={keywordInput}
              setKeywordInput={setKeywordInput}
              addKeywordTag={addKeywordTag}
              removeKeywordTag={removeKeywordTag}
              toggleJobType={toggleJobType}
              setPreferences={setPreferences}
              errors={profileErrors}
              onSave={handleSaveProfile}
            />
          ) : (
            <section className="panel">Vui lòng đăng nhập để vào trang profile.</section>
          )
        )}
        {activePage === "detail" && (
          <JobDetailPanel
            job={selectedJob}
            analysis={jobAnalysis}
            onBack={() => setActivePage(detailBackPage)}
            onAnalyze={handleAnalyzeSelectedJob}
            onSaveJob={handleSaveJob}
            onApplyJob={handleApplyJob}
          />
        )}
      </main>
    </div>
  );
}

function AuthRoutePage(props) {
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
  setAuthMode,
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
          <form className="auth-form" onSubmit={handleLoginSubmit}>
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
            <button className="primary-btn" type="submit" disabled={loading}>
              Login
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
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
            <button className="primary-btn" type="submit" disabled={loading}>
              Register
            </button>
          </form>
        )}

        <div className="status-chip">{statusMessage}</div>
        <button className="ghost-btn full-width" type="button" onClick={closeAuthRoute}>
          Close
        </button>
      </div>
    </section>
  );
}

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

function DashboardPanel({ overview, stats, token, onOpenRecommendations }) {
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

function AnalysisWorkspace({
  mode,
  setMode,
  analysisForm,
  setAnalysisForm,
  onAnalyzeSingle,
  batchText,
  setBatchText,
  batchAnalysis,
  onAnalyzeBatch,
  jobs,
  total,
  query,
  risk,
  page,
  totalPages,
  setQuery,
  setRisk,
  onSearch,
  onPrevious,
  onNext,
  onPickJob,
  onOpenJob,
  onSaveJob,
  onApplyJob,
}) {
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
        <section className="panel-grid double">
          <div className="panel panel-stack">
            <div className="detail-grid">
              <Field label="Job title" value={analysisForm.title} onChange={(value) => setAnalysisForm((current) => ({ ...current, title: value }))} maxLength={160} />
              <Field
                label="Tên công ty"
                value={analysisForm.companyName}
                onChange={(value) => setAnalysisForm((current) => ({ ...current, companyName: value }))}
                maxLength={160}
              />
              <Field label="Mức lương" value={analysisForm.salary} onChange={(value) => setAnalysisForm((current) => ({ ...current, salary: value }))} maxLength={120} />
              <Field label="Địa chỉ" value={analysisForm.address} onChange={(value) => setAnalysisForm((current) => ({ ...current, address: value }))} maxLength={160} />
              <Field label="Email" value={analysisForm.email} onChange={(value) => setAnalysisForm((current) => ({ ...current, email: value }))} maxLength={160} />
              <Field label="Số điện thoại" value={analysisForm.phone} onChange={(value) => setAnalysisForm((current) => ({ ...current, phone: value }))} maxLength={40} />
            </div>
            <label>
              <span>Mô tả</span>
              <textarea rows="6" value={analysisForm.description} onChange={(event) => setAnalysisForm((current) => ({ ...current, description: event.target.value.slice(0, 2500) }))} maxLength={2500} />
            </label>
            <label>
              <span>Yêu cầu</span>
              <textarea rows="4" value={analysisForm.requirements} onChange={(event) => setAnalysisForm((current) => ({ ...current, requirements: event.target.value.slice(0, 1800) }))} maxLength={1800} />
            </label>
            <div className="card-actions">
              <button className="primary-btn" type="button" onClick={onAnalyzeSingle}>
                Phân tích tin này
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
              <select value={risk} onChange={(event) => setRisk(event.target.value)}>
                <option value="ALL">Tất cả mức rủi ro</option>
                <option value="LOW">Thấp</option>
                <option value="MEDIUM">Trung bình</option>
                <option value="HIGH">Cao</option>
              </select>
              <button className="primary-btn" type="submit">Tìm</button>
            </form>
            <div className="quick-job-list">
              {jobs.map((job) => (
                <article key={job.id} className="quick-job-card">
                  <div>
                    <strong>{job.title}</strong>
                    <p className="muted">{job.companyName || "Unknown company"}</p>
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
            <textarea rows="20" value={batchText} onChange={(event) => setBatchText(event.target.value.slice(0, 12000))} maxLength={12000} />
            <button className="primary-btn" type="button" onClick={onAnalyzeBatch}>
              Phân tích nhiều tin
            </button>
          </div>

          <div className="panel panel-stack">
            <h3>Kết quả batch</h3>
            {!batchAnalysis && <p className="muted">Chưa có kết quả. Bấm phân tích để xem danh sách đánh giá.</p>}
            {batchAnalysis && (
              <>
                <div className="summary-grid">
                  <StatCard title="Tổng tin" value={batchAnalysis.summary?.total || 0} accent="blue" />
                  <StatCard title="Trust TB" value={`${batchAnalysis.summary?.averageTrustScore || 0}%`} accent="green" />
                  <StatCard title="Thấp" value={batchAnalysis.summary?.riskLevels?.LOW || 0} accent="amber" />
                  <StatCard title="Cao" value={batchAnalysis.summary?.riskLevels?.HIGH || 0} accent="red" />
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
                      <div className="job-card-top">
                        <span className={`pill ${(item.result?.riskLevel || "LOW").toLowerCase()}`}>{item.result?.riskLabel || item.result?.riskLevel}</span>
                        <strong>{Math.round(item.result?.trustScore || 0)}% trust</strong>
                      </div>
                      <h4>{item.job?.title || "Untitled job"}</h4>
                      <p>{item.job?.companyName || "Unknown company"}</p>
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

function JobDetailPanel({ job, analysis, onBack, onAnalyze, onSaveJob, onApplyJob }) {
  if (!job) {
    return <section className="panel">Hãy chọn một job từ Job List để xem chi tiết.</section>;
  }

  return (
    <section className="panel-grid double">
      <div className="panel panel-stack">
        <div className="section-heading">
          <div>
            <h3>Job Detail</h3>
            <p className="muted">Xem thông tin job và chạy phân tích độ uy tín trực tiếp.</p>
          </div>
          <button className="secondary-btn" onClick={onBack}>Back to list</button>
        </div>
        <div className="detail-grid">
          <DetailItem label="Title" value={job.title} />
          <DetailItem label="Company" value={job.companyName || "Unknown"} />
          <DetailItem label="Location" value={job.location || "Toàn quốc"} />
          <DetailItem label="Salary" value={job.salary || "Đang cập nhật"} />
          <DetailItem label="Risk level" value={job.riskLabel || job.riskLevel} />
          <DetailItem label="Trust score" value={`${Math.round(job.trustScore || 0)}%`} />
        </div>
        <div className="card-actions">
          <button className="secondary-btn" onClick={() => onSaveJob(job)}>Save</button>
          <button className="ghost-btn" onClick={() => onApplyJob(job)}>Apply</button>
          <button className="primary-btn" onClick={onAnalyze}>Analyze</button>
        </div>
      </div>

      <div className="panel panel-stack">
        <h3>Analysis</h3>
        {!analysis && <p className="muted">Chưa có kết quả phân tích. Bấm Analyze để xem risk score, cảnh báo và blacklist match.</p>}
        {analysis && (
          <>
            <div className="stats-grid compact-grid">
              <StatCard title="Risk score" value={`${analysis.result?.riskScore || 0}%`} accent="red" />
              <StatCard title="Trust score" value={`${analysis.result?.trustScore || 0}%`} accent="green" />
            </div>
            <div className="metric-list">
              <div className="metric-row">
                <span>Decision</span>
                <strong>{analysis.result?.decision}</strong>
              </div>
              <div className="metric-row">
                <span>Blacklist</span>
                <strong>{analysis.blacklist?.hasMatch ? "Matched" : "Safe"}</strong>
              </div>
            </div>
            <div className="detail-block">
              <h4>Warning signals</h4>
              {(analysis.signals || []).length === 0 && <p className="muted">Chưa ghi nhận tín hiệu rủi ro rõ ràng.</p>}
              <ul>
                {(analysis.signals || []).map((signal) => (
                  <li key={signal}>{signal}</li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function SavedJobsPanel({ savedJobs, onApply, onDelete, onNoteSave }) {
  return (
    <section className="panel-grid">
      <div className="section-heading">
        <div>
          <h3>Saved Jobs</h3>
          <p className="muted">Trang này hỗ trợ note editable và apply nhanh để đẩy job sang Applications.</p>
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
      <div className="job-card-top">
        <span className={`pill ${(item.riskLevel || "LOW").toLowerCase()}`}>{getRiskLabel(item.riskLevel)}</span>
        <strong>{Math.round(item.trustScore || 0)}% trust</strong>
      </div>
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

function ApplicationsPanel({ columns, groups, onDropStatus, onDelete, onOpenJob }) {
  return (
    <section className="panel-grid">
      <div className="section-heading">
        <div>
          <h3>Applications Kanban</h3>
          <p className="muted">Thẻ được rút gọn còn tiêu đề công việc để dễ nhìn hơn. Kéo thả để đổi trạng thái hoặc bấm vào thẻ để mở job detail.</p>
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
      <div className="job-card-top">
        <span className={`pill ${(item.riskLevel || "LOW").toLowerCase()}`}>{getRiskLabel(item.riskLevel)}</span>
        <strong>{Math.round(item.trustScore || 0)}%</strong>
      </div>
      <h4>{item.job?.title || "Untitled job"}</h4>
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

function BlacklistPanel({
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

function StatisticsPanel({ stats, riskSummary, token }) {
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
        <StatCard title="Avg trust" value={stats.averageTrustScore} accent="green" />
        <StatCard title="Success rate" value={`${stats.successRate}%`} accent="red" />
      </div>

      <div className="panel-grid double">
        <div className="panel">
          <h3>Status distribution</h3>
          <div className="bar-list">
            {(stats.statusDistribution || []).map((item) => (
              <BarRow key={item.status} label={item.label} value={item.count} max={stats.total || 1} />
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Risk distribution</h3>
          <div className="pie-legend">
            {(stats.riskDistribution || []).map((item) => (
              <div key={item.riskLevel} className="legend-row">
                <span className={`legend-dot ${(item.riskLevel || "").toLowerCase()}`} />
                <span>{item.label}</span>
                <strong>{item.count}</strong>
              </div>
            ))}
          </div>
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
            <div className="metric-row">
              <span>High risk applied</span>
              <strong>{riskSummary?.highRiskApplied || 0}</strong>
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

function ProfilePanel({
  preferences,
  keywordInput,
  setKeywordInput,
  addKeywordTag,
  removeKeywordTag,
  toggleJobType,
  setPreferences,
  errors,
  onSave,
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
            {JOB_TYPE_OPTIONS.map((jobType) => {
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

function StatCard({ title, value, accent }) {
  return (
    <div className={`stat-card ${accent}`}>
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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

function validateLogin(values) {
  const errors = {};
  if (!isValidEmail(values.email)) errors.email = "Email chưa hợp lệ.";
  if (!values.password) errors.password = "Vui lòng nhập password.";
  if ((values.password || "").length > 72) errors.password = "Password không được vượt quá 72 ký tự.";
  return errors;
}

function validateRegister(values) {
  const errors = {};
  if (!values.name.trim()) errors.name = "Vui lòng nhập tên.";
  if ((values.name || "").trim().length > 80) errors.name = "Tên không được vượt quá 80 ký tự.";
  if (!isValidEmail(values.email)) errors.email = "Email chưa hợp lệ.";
  if ((values.password || "").length < 6) errors.password = "Password phải từ 6 ký tự.";
  if ((values.password || "").length > 72) errors.password = "Password không được vượt quá 72 ký tự.";
  if (values.confirmPassword !== values.password) errors.confirmPassword = "Confirm password chưa khớp.";
  return errors;
}

function validateProfile(values) {
  const errors = {};
  if (!values.name.trim()) errors.name = "Name không được để trống.";
  if ((values.name || "").trim().length > 80) errors.name = "Name không được vượt quá 80 ký tự.";
  if ((values.keywords || []).length > 12) errors.general = "Tối đa 12 keyword.";
  if (!Array.isArray(values.preferredRisk) || values.preferredRisk.length === 0) {
    errors.general = "Hãy chọn ít nhất một mức rủi ro ưu tiên.";
  }
  return errors;
}

function validateBlacklist(values) {
  const errors = {};
  const invalidEmails = values.emails.filter((email) => !isValidEmail(email));
  const invalidPhones = values.phones.filter((phone) => !/^[0-9+\s().-]{8,20}$/.test(phone));
  if (invalidEmails.length > 0) errors.emailsText = "Có email chưa đúng định dạng.";
  if (invalidPhones.length > 0) errors.phonesText = "Có số điện thoại chưa đúng định dạng.";
  return errors;
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}

function loadPreferences() {
  try {
    const raw = localStorage.getItem(APP_PREFERENCES_KEY);
    if (!raw) return DEFAULT_PROFILE;
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_PROFILE,
      ...parsed,
      keywords: Array.isArray(parsed.keywords) ? parsed.keywords : DEFAULT_PROFILE.keywords,
      jobTypes: Array.isArray(parsed.jobTypes) ? parsed.jobTypes : DEFAULT_PROFILE.jobTypes,
      preferredRisk: Array.isArray(parsed.preferredRisk) && parsed.preferredRisk.length
        ? parsed.preferredRisk
        : DEFAULT_PROFILE.preferredRisk,
    };
  } catch (error) {
    return DEFAULT_PROFILE;
  }
}

function mergeProfilePreferences(current, profile) {
  const preferences = profile?.preferences || {};
  return {
    ...current,
    name: profile?.name || current.name || "",
    email: profile?.email || current.email || "",
    keywords: Array.isArray(preferences.keywords) ? preferences.keywords : current.keywords,
    jobTypes: Array.isArray(preferences.jobTypes) ? preferences.jobTypes : current.jobTypes,
    preferredRisk: Array.isArray(preferences.preferredRisk) && preferences.preferredRisk.length
      ? preferences.preferredRisk
      : current.preferredRisk,
  };
}

function loadUserBlacklist(ownerKey) {
  try {
    if (!ownerKey) return [];
    const raw = localStorage.getItem(USER_BLACKLIST_STORAGE_KEY);
    const parsed = JSON.parse(raw || "{}");
    const items = parsed?.[ownerKey];
    return Array.isArray(items) ? items : [];
  } catch (error) {
    return [];
  }
}

function saveUserBlacklist(ownerKey, items) {
  try {
    const raw = localStorage.getItem(USER_BLACKLIST_STORAGE_KEY);
    const parsed = JSON.parse(raw || "{}");
    parsed[ownerKey] = Array.isArray(items) ? items : [];
    localStorage.setItem(USER_BLACKLIST_STORAGE_KEY, JSON.stringify(parsed));
  } catch (error) {
    localStorage.setItem(USER_BLACKLIST_STORAGE_KEY, JSON.stringify({ [ownerKey]: Array.isArray(items) ? items : [] }));
  }
}

function mapJobToAnalysisForm(job = {}) {
  return {
    title: job.title || "",
    companyName: job.companyName || "",
    description: job.description || "",
    requirements: job.requirements || "",
    benefits: job.benefits || "",
    salary: job.salary || "",
    address: job.address || job.location || "",
    email: job.email || "",
    phone: job.phone || "",
    companySize: job.companySize || "",
    experience: job.experience || "",
    careerLevel: job.careerLevel || "",
    jobType: job.jobType || "",
  };
}

function mapJobToAnalysisPayload(job = {}) {
  return {
    ...mapJobToAnalysisForm(job),
    candidates: Number(job.candidates || 0),
  };
}

function buildTrackingPayload(job) {
  return {
    jobId: job?.id ?? null,
    riskScore: Number(job?.riskScore || 0),
    trustScore: Number(job?.trustScore || 0),
    riskLevel: job?.riskLevel || "",
    job: {
      title: job?.title || "",
      companyName: job?.companyName || "",
      salary: job?.salary || "",
      location: job?.location || job?.address || "",
      description: [job?.description, job?.requirements, job?.benefits].filter(Boolean).join("\n"),
    },
  };
}

function findCount(items = [], key) {
  return items.find((item) => item.status === key)?.count || 0;
}

function buildRiskPercent(summary = {}) {
  const total = Number(summary.totalJobs || 0);
  const risky = Number(summary.mediumRiskJobs || 0) + Number(summary.highRiskJobs || 0);
  return total ? `${Math.round((risky / total) * 100)}%` : "0%";
}

function buildAvatarLabel(name) {
  const text = String(name || "").trim();
  if (!text) return "G";
  return text
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");
}

function getRiskLabel(level) {
  return {
    LOW: "Thấp",
    MEDIUM: "Trung bình",
    HIGH: "Cao",
  }[String(level || "").toUpperCase()] || String(level || "Thấp");
}

function matchUserBlacklist(items = [], target = {}) {
  const title = String(target.title || "").trim().toLowerCase();
  const companyName = String(target.companyName || "").trim().toLowerCase();

  return items.filter((item) => {
    const itemTitle = String(item.title || "").trim().toLowerCase();
    const itemCompany = String(item.companyName || "").trim().toLowerCase();
    const titleMatch = itemTitle && title.includes(itemTitle);
    const companyMatch = itemCompany && companyName.includes(itemCompany);
    return titleMatch || companyMatch;
  });
}
