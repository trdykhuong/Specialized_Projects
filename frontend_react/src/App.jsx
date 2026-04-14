import { useEffect, useMemo, useState } from "react";
import { api, authStorage } from "./api";
import { sampleBatchText } from "./mockData";

const APP_PREFERENCES_KEY = "jobtrust_profile_preferences";
const USER_BLACKLIST_STORAGE_KEY = "jobtrust_user_blacklist";
const JOB_TYPE_OPTIONS = ["Toàn thời gian", "Bán thời gian", "Remote", "Hybrid", "Thực tập", "Freelance"];
const KANBAN_COLUMNS = [
  { id: "applied", label: "Applied" },
  { id: "interviewing", label: "Interviewing" },
  { id: "offered", label: "Offered" },
  { id: "rejected", label: "Rejected" },
];
const STATUS_OPTIONS = [
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offered", label: "Offered" },
  { value: "rejected", label: "Rejected" },
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
  title: "",
  companyName: "",
  description: "",
  requirements: "",
  benefits: "",
  salary: "",
  address: "",
  email: "",
  phone: "",
  companySize: "",
  experience: "",
  careerLevel: "",
  jobType: "",
  submissionDeadline: "",
  candidates: "",
};

const DEFAULT_USER_BLACKLIST_FORM = {
  title: "",
  companyName: "",
};

const menuSections = [
  {
    title: "Workspace",
    items: [
      { id: "analysis", label: "Analysis" },
      { id: "saved", label: "Saved Jobs" },
      { id: "applications", label: "Applications" },
      { id: "statistics", label: "Statistic" },
    ],
  },
  {
    title: "Safety & Account",
    items: [
      { id: "blacklist", label: "Blacklist" },
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
  const [jobs, setJobs] = useState([]);
  const [jobQuery, setJobQuery] = useState("");
  const [jobPage, setJobPage] = useState(1);
  const [jobTotalPages, setJobTotalPages] = useState(0);
  const [jobTotal, setJobTotal] = useState(0);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobAnalysis, setJobAnalysis] = useState(null);
  const [detailBackPage, setDetailBackPage] = useState("analysis");
  const [detailViewMode, setDetailViewMode] = useState("analysis");
  const [analysisMode, setAnalysisMode] = useState("single");
  const [analysisForm, setAnalysisForm] = useState(DEFAULT_ANALYSIS_FORM);
  const [analysisFormSource, setAnalysisFormSource] = useState("manual");
  const [batchText, setBatchText] = useState(sampleBatchText);
  const [batchAnalysis, setBatchAnalysis] = useState(null);
  const [stats, setStats] = useState(null);
  const [blacklist, setBlacklist] = useState({ companies: [], emails: [], phones: [] });
  const [blacklistCheckForm, setBlacklistCheckForm] = useState(DEFAULT_BLACKLIST_CHECK);
  const [blacklistCheckResult, setBlacklistCheckResult] = useState(null);
  const [userBlacklist, setUserBlacklist] = useState([]);
  const [userBlacklistLoadedKey, setUserBlacklistLoadedKey] = useState("");
  const [userBlacklistForm, setUserBlacklistForm] = useState(DEFAULT_USER_BLACKLIST_FORM);
  const [loading, setLoading] = useState(false);
  const [analysisRequest, setAnalysisRequest] = useState({ pending: false, context: "", error: "", message: "" });
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
        const jobsData = await api.getJobs({ page: 1, pageSize: 9 });
        if (ignore) return;
        setJobs(jobsData.items || []);
        setJobTotal(jobsData.total || 0);
        setJobTotalPages(jobsData.totalPages || 0);
        setJobPage(jobsData.page || 1);
        setSelectedJob((current) => current || jobsData.items?.[0] || null);
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
        const [profile, savedData, applicationsData, statsData] = await Promise.all([
          api.getProfile(),
          api.getSavedJobs(),
          api.getApplications({ pageSize: 100 }),
          api.getStatistics(),
        ]);
        if (ignore) return;
        setUser(profile);
        setPreferences((current) => mergeProfilePreferences(current, profile));
        setSavedJobs(savedData.items || []);
        setApplications(applicationsData.items || []);
        setStats(statsData);
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
  }, [token]);

  const applicationGroups = useMemo(() => {
    const groups = Object.fromEntries(KANBAN_COLUMNS.map((column) => [column.id, []]));
    applications.forEach((application) => {
      const normalizedStatus = application.status === "saved" ? "applied" : application.status;
      const key = groups[normalizedStatus] ? normalizedStatus : "rejected";
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
    setActivePage("analysis");
    setStatusMessage("Bạn đang ở chế độ guest.");
    setAccountMenuOpen(false);
    closeAuthRoute();
  }

  async function refreshUserData(message) {
    if (!token) return;
    const [savedData, applicationsData, statsData] = await Promise.all([
      api.getSavedJobs(),
      api.getApplications({ pageSize: 100 }),
      api.getStatistics(),
    ]);
    setSavedJobs(savedData.items || []);
    setApplications(applicationsData.items || []);
    setStats(statsData);
    if (message) {
      setStatusMessage(message);
    }
  }

  async function loadJobs(page = 1, query = jobQuery) {
    try {
      const data = await api.getJobs({ page, pageSize: 9, query });
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
    setAnalysisRequest({
      pending: true,
      context: "detail",
      error: "",
      message: "Đang phân tích tin tuyển dụng. Vui lòng chờ trong giây lát...",
    });
    try {
      const payload = mapJobToAnalysisPayload(selectedJob);
      const result = enrichAnalysisResult(await api.analyzeJob(payload), selectedJob, blacklist, userBlacklist);
      setJobAnalysis(result);
      setActivePage("detail");
      setAnalysisRequest({
        pending: false,
        context: "detail",
        error: "",
        message: "Phân tích hoàn tất. Đã cập nhật điểm rủi ro và mức độ nguy hiểm.",
      });
      setStatusMessage("Đã phân tích độ uy tín cho job đang chọn.");
    } catch (error) {
      setAnalysisRequest({
        pending: false,
        context: "detail",
        error: error.message || "Không phân tích được job. Vui lòng kiểm tra dữ liệu đầu vào rồi thử lại.",
        message: "",
      });
      setStatusMessage(error.message || "Không phân tích được job.");
    }
  }

  async function handleAnalyzeSingle() {
    setAnalysisRequest({
      pending: true,
      context: "single",
      error: "",
      message: "Đang gửi dữ liệu để phân tích. Hệ thống sẽ trả về điểm rủi ro ngay khi hoàn tất...",
    });
    try {
      const result = enrichAnalysisResult(await api.analyzeJob(analysisForm), analysisForm, blacklist, userBlacklist);
      let detailJob = result.job || analysisForm;
      if (analysisFormSource === "manual") {
        const createdJob = await api.createJob({
          ...mapJobToAnalysisPayload(analysisForm),
          source: "manual",
        });
        detailJob = { ...detailJob, ...createdJob, ...analysisForm };
      } else {
        detailJob = { ...detailJob, ...analysisForm };
      }
      setSelectedJob(detailJob);
      setJobAnalysis(result);
      setDetailBackPage("analysis");
      setActivePage("detail");
      setAnalysisRequest({
        pending: false,
        context: "single",
        error: "",
        message: "Phân tích hoàn tất. Kết quả rủi ro đã sẵn sàng.",
      });
      setStatusMessage("Đã phân tích 1 tin tuyển dụng.");
    } catch (error) {
      setAnalysisRequest({
        pending: false,
        context: "single",
        error: error.message || "Phân tích thất bại. Vui lòng kiểm tra mô tả, email hoặc thông tin công ty.",
        message: "",
      });
      setStatusMessage(error.message || "Không phân tích được tin tuyển dụng.");
    }
  }

  async function handleAnalyzeBatch() {
    setAnalysisRequest({
      pending: true,
      context: "batch",
      error: "",
      message: "Đang tách và phân tích danh sách tin tuyển dụng. Quá trình này có thể mất thêm chút thời gian...",
    });
    try {
      const result = await api.batchAnalyze({ rawText: batchText });
      setBatchAnalysis(result);
      setAnalysisMode("batch");
      setAnalysisRequest({
        pending: false,
        context: "batch",
        error: "",
        message: "Đã phân tích xong danh sách tin tuyển dụng.",
      });
      setStatusMessage("Đã phân tích nhiều tin tuyển dụng.");
    } catch (error) {
      setAnalysisRequest({
        pending: false,
        context: "batch",
        error: error.message || "Không phân tích được danh sách tin. Hãy thử tách mỗi tin bằng một dòng trống.",
        message: "",
      });
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
    const { backPage = "analysis", analysis = null, viewMode = "analysis" } = options;
    setSelectedJob(job);
    setJobAnalysis(analysis || null);
    setDetailBackPage(backPage);
    setDetailViewMode(viewMode);
    setActivePage("detail");
  }

  function handlePickQuickJob(job) {
    setAnalysisForm(mapJobToAnalysisForm(job));
    setAnalysisFormSource("existing");
    setSelectedJob(job);
    setStatusMessage("Đã đưa tin tuyển dụng vào form phân tích.");
  }

  async function handleOpenApplicationJob(item) {
    const fallbackJob = {
      ...item.job,
      id: item.jobId || item.job?.id || item.id,
    };

    if (item.jobId) {
      try {
        const fullJob = await api.getJob(item.jobId);
        openJobDetail(
          {
            ...fallbackJob,
            ...fullJob,
          },
          { backPage: "applications", viewMode: "form" }
        );
        return;
      } catch (error) {
        // Fall back to stored snapshot if the dataset record is unavailable.
      }
    }

    openJobDetail(fallbackJob, { backPage: "applications", viewMode: "form" });
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
                  <button className="ghost-btn full-width" onClick={() => { handleLogout(); setAccountMenuOpen(false); }}>
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {activePage === "analysis" && (
          <AnalysisWorkspace
            mode={analysisMode}
            setMode={setAnalysisMode}
            analysisForm={analysisForm}
            setAnalysisForm={setAnalysisForm}
            onAnalyzeSingle={handleAnalyzeSingle}
            analysisRequest={analysisRequest}
            batchText={batchText}
            setBatchText={setBatchText}
            batchAnalysis={batchAnalysis}
            onAnalyzeBatch={handleAnalyzeBatch}
            jobs={jobs}
            total={jobTotal}
            query={jobQuery}
            page={jobPage}
            totalPages={jobTotalPages}
            setQuery={setJobQuery}
            onSearch={() => loadJobs(1, jobQuery)}
            onPrevious={() => loadJobs(Math.max(1, jobPage - 1), jobQuery)}
            onNext={() => loadJobs(Math.min(jobTotalPages || 1, jobPage + 1), jobQuery)}
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
            token={Boolean(token)}
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
            viewMode={detailViewMode}
            analysisRequest={analysisRequest}
            systemBlacklist={blacklist}
            userBlacklist={userBlacklist}
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
              <FunnelStep label="Saved"  value={stats?.savedCount || 0} />
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
  analysisRequest,
  batchText,
  setBatchText,
  batchAnalysis,
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
              <Field label="Hạn chót nộp hồ sơ" value={analysisForm.submissionDeadline} onChange={(value) => setAnalysisForm((current) => ({ ...current, submissionDeadline: value }))} maxLength={80} />
              <Field label="Số lượng ứng viên" value={analysisForm.candidates} onChange={(value) => setAnalysisForm((current) => ({ ...current, candidates: value }))} maxLength={40} />
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
            {batchAnalyzeError && <div className="error-banner">{batchAnalyzeError}</div>}
            {batchAnalyzeMessage && <div className={batchAnalyzePending ? "status-banner pending" : "status-banner success"}>{batchAnalyzeMessage}</div>}
            <textarea rows="20" value={batchText} onChange={(event) => setBatchText(event.target.value.slice(0, 12000))} maxLength={12000} />
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
                      <h4>{item.job?.title || "Untitled job"}</h4>
                      <p>{item.job?.companyName || "Unknown company"}</p>
                      <p className="muted">{item.job?.address || "Chưa có địa chỉ"} • {item.job?.salary || "Không có "}</p>
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

function JobDetailPanel({ job, analysis, viewMode = "analysis", analysisRequest, systemBlacklist, userBlacklist, onBack, onAnalyze, onSaveJob, onApplyJob }) {
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
    { label: "Job title", value: normalizedJob.title, type: "field" },
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
    { label: "Company Size", value: normalizedJob.companySize },
    { label: "Job Type", value: normalizedJob.jobType },
    { label: "Number Cadidate", value: normalizedJob.candidates },
    { label: "Career Level", value: normalizedJob.careerLevel },
    { label: "Years of Experience", value: normalizedJob.experience },
    { label: "Submission Deadline", value: normalizedJob.submissionDeadline },
  ];

  return (
    <section className={layoutClassName}>
      <div className="panel panel-stack">
        <div className="section-heading">
          <div>
            <h3>Job Detail</h3>
            <p className="muted">Xem thông tin job và chạy phân tích độ uy tín trực tiếp.</p>
          </div>
          <button className="secondary-btn" onClick={onBack}>Back to list</button>
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
              <button className="secondary-btn" onClick={() => onSaveJob(job)}>Save</button>
              <button className="ghost-btn" onClick={() => onApplyJob(job)}>Apply</button>
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
              <button className="secondary-btn" onClick={() => onSaveJob(job)}>Save</button>
              <button className="ghost-btn" onClick={() => onApplyJob(job)}>Apply</button>
              <button className="primary-btn" onClick={onAnalyze} disabled={detailAnalyzePending}>
                {detailAnalyzePending ? "Đang phân tích..." : "Analyze"}
              </button>
            </div>
          </>
        )}
      </div>

      {showAnalysisPanel && (
        <div className="panel panel-stack">
          <h3>Analysis</h3>
          {!analysisWithBlacklist && <p className="muted">Chưa có kết quả phân tích. Bấm Analyze nếu bạn muốn xem cảnh báo nội dung và đối chiếu blacklist.</p>}
          {analysisWithBlacklist && (
            <>
              <div className="analysis-score-grid">
                <div className="score-card risk">
                  <span>Risk score</span>
                  <strong>{analysisSummary.riskScore}</strong>
                </div>
                <div className="score-card trust">
                  <span>Trust score</span>
                  <strong>{analysisSummary.trustScore}</strong>
                </div>
              </div>
              <div className="metric-list">
                <div className="metric-row">
                  <span>Mức độ nguy hiểm</span>
                  <strong>{analysisSummary.riskLevel}</strong>
                </div>
                <div className="metric-row">
                  <span>Decision</span>
                  <strong>{analysisSummary.decision}</strong>
                </div>
                <div className="metric-row">
                  <span>Blacklist chung</span>
                  <strong>{analysisWithBlacklist.blacklist?.system?.hasMatch ? "Matched" : "Safe"}</strong>
                </div>
                <div className="metric-row">
                  <span>Blacklist cá nhân</span>
                  <strong>{analysisWithBlacklist.blacklist?.personal?.hasMatch ? "Matched" : "Safe"}</strong>
                </div>
                <div className="metric-row">
                  <span>Đối chiếu tổng</span>
                  <strong>{analysisWithBlacklist.blacklist?.hasMatch ? "Matched" : "Safe"}</strong>
                </div>
                <div className="metric-row">
                  <span>Số cảnh báo</span>
                  <strong>{analysisWithBlacklist.signals?.length || 0}</strong>
                </div>
              </div>
              <div className="detail-block">
                <h4>Warning signals</h4>
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

function StatisticsPanel({ stats, token }) {
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
  const normalizedJob = normalizeJobRecord(job);
  return {
    title: normalizedJob.title || "",
    companyName: normalizedJob.companyName || "",
    description: normalizedJob.description || "",
    requirements: normalizedJob.requirements || "",
    benefits: normalizedJob.benefits || "",
    salary: normalizedJob.salary || "",
    address: normalizedJob.address || normalizedJob.location || "",
    email: normalizedJob.email || "",
    phone: normalizedJob.phone || "",
    companySize: normalizedJob.companySize || "",
    experience: normalizedJob.experience || "",
    careerLevel: normalizedJob.careerLevel || "",
    jobType: normalizedJob.jobType || "",
    submissionDeadline: normalizedJob.submissionDeadline || "",
    candidates: normalizedJob.candidates || "",
  };
}

function mapJobToAnalysisPayload(job = {}) {
  const normalizedJob = normalizeJobRecord(job);
  return {
    ...mapJobToAnalysisForm(job),
    candidates: Number(normalizedJob.candidates || 0),
    submissionDeadline: normalizedJob.submissionDeadline || "",
  };
}

function buildTrackingPayload(job) {
  const normalizedJob = normalizeJobRecord(job);
  return {
    jobId: normalizedJob?.id ?? null,
    job: {
      title: normalizedJob?.title || "",
      jobTitle: normalizedJob?.title || "",
      companyName: normalizedJob?.companyName || "",
      nameCompany: normalizedJob?.companyName || "",
      companyOverview: normalizedJob?.companyOverview || "",
      companySize: normalizedJob?.companySize || "",
      companyAddress: normalizedJob?.companyAddress || "",
      salary: normalizedJob?.salary || "",
      location: normalizedJob?.location || normalizedJob?.address || "",
      address: normalizedJob?.address || normalizedJob?.location || "",
      jobAddress: normalizedJob?.jobAddress || normalizedJob?.address || normalizedJob?.location || "",
      email: normalizedJob?.email || "",
      phone: normalizedJob?.phone || "",
      description: normalizedJob?.description || "",
      requirements: normalizedJob?.requirements || "",
      benefits: normalizedJob?.benefits || "",
      jobType: normalizedJob?.jobType || "",
      gender: normalizedJob?.gender || "",
      candidates: normalizedJob?.candidates || "",
      numberCadidate: normalizedJob?.candidates || "",
      careerLevel: normalizedJob?.careerLevel || "",
      experience: normalizedJob?.experience || "",
      yearsOfExperience: normalizedJob?.experience || "",
      submissionDeadline: normalizedJob?.submissionDeadline || "",
      industry: normalizedJob?.industry || "",
    },
  };
}

function findCount(items = [], key) {
  return items.find((item) => item.status === key)?.count || 0;
}

function normalizeJobRecord(job = {}) {
  return {
    id: getRecordValue(job, ["id", "jobId", "JobID"]),
    urlJob: getRecordValue(job, ["urlJob", "url", "jobUrl", "URL Job"]),
    title: getRecordValue(job, ["title", "jobTitle", "Job Title"]) || "",
    companyName: getRecordValue(job, ["companyName", "nameCompany", "company", "Name Company"]) || "",
    companyOverview: getRecordValue(job, ["companyOverview", "overview", "Company Overview"]) || "",
    companySize: getRecordValue(job, ["companySize", "Company Size"]) || "",
    companyAddress: getRecordValue(job, ["companyAddress", "Company Address"]) || "",
    description: getRecordValue(job, ["description", "jobDescription", "Job Description"]) || "",
    requirements: getRecordValue(job, ["requirements", "jobRequirements", "Job Requirements"]) || "",
    benefits: getRecordValue(job, ["benefits", "Benefits"]) || "",
    jobAddress: getRecordValue(job, ["jobAddress", "Job Address"]) || "",
    address: getRecordValue(job, ["address", "jobAddress", "Job Address"]) || "",
    location: getRecordValue(job, ["location", "address", "jobAddress", "Job Address"]) || "",
    jobType: getRecordValue(job, ["jobType", "Job Type"]) || "",
    gender: getRecordValue(job, ["gender", "Gender"]) || "",
    candidates: getRecordValue(job, ["candidates", "numberCandidate", "numberCadidate", "Number Cadidate"]) || "",
    careerLevel: getRecordValue(job, ["careerLevel", "Career Level"]) || "",
    experience: getRecordValue(job, ["experience", "yearsOfExperience", "Years of Experience"]) || "",
    salary: getRecordValue(job, ["salary", "Salary"]) || "",
    submissionDeadline: getRecordValue(job, ["submissionDeadline", "Submission Deadline"]) || "",
    industry: getRecordValue(job, ["industry", "Industry"]) || "",
    email: getRecordValue(job, ["email", "Email", "companyEmail", "contactEmail"]) || "",
    phone: getRecordValue(job, ["phone", "Phone", "companyPhone", "contactPhone", "Số điện thoại"]) || "",
  };
}

function getRecordValue(record, keys = []) {
  for (const key of keys) {
    if (record?.[key] !== undefined && record?.[key] !== null && record?.[key] !== "") {
      return record[key];
    }
  }
  return "";
}

function enrichAnalysisResult(analysis, job, systemBlacklist, userBlacklist) {
  if (!analysis) return analysis;
  const normalizedJob = normalizeJobRecord(job);
  const systemMatch = matchSystemBlacklist(systemBlacklist, normalizedJob);
  const personalMatchItems = matchUserBlacklist(userBlacklist, normalizedJob);
  const backendHasMatch = Boolean(analysis?.blacklist?.hasMatch);
  const mergedSignals = mergeSignals(
    analysis?.signals,
    buildMissingFieldSignals(normalizedJob),
    systemMatch.hasMatch ? systemMatch.details.map((item) => `Blacklist chung: ${item}`) : [],
    personalMatchItems.length > 0 ? personalMatchItems.map((item) => `Blacklist cá nhân: ${item.title || item.companyName}`) : []
  );

  return {
    ...analysis,
    signals: mergedSignals,
    blacklist: {
      ...(analysis?.blacklist || {}),
      hasMatch: backendHasMatch || systemMatch.hasMatch || personalMatchItems.length > 0,
      system: systemMatch,
      personal: {
        hasMatch: personalMatchItems.length > 0,
        items: personalMatchItems,
      },
    },
  };
}

function buildAnalysisSummary(analysis) {
  const trustRaw = firstDefined(
    analysis?.trustScore,
    analysis?.trust_score,
    analysis?.result?.trustScore,
    analysis?.result?.trust_score,
    analysis?.scores?.trust,
    analysis?.scores?.trustScore,
    analysis?.trust?.score,
    analysis?.trust
  );
  const riskRaw = firstDefined(
    analysis?.riskScore,
    analysis?.risk_score,
    analysis?.result?.riskScore,
    analysis?.result?.risk_score,
    analysis?.riskPercent,
    analysis?.risk_probability,
    analysis?.scores?.risk,
    analysis?.scores?.riskScore,
    analysis?.risk?.score,
    analysis?.risk
  );
  const trustValue = normalizePercent(trustRaw);
  const riskValue = normalizePercent(riskRaw);
  const resolvedRiskValue = riskValue ?? (trustValue != null ? Math.max(0, 100 - trustValue) : null);
  const resolvedTrustValue = trustValue ?? (resolvedRiskValue != null ? Math.max(0, 100 - resolvedRiskValue) : null);
  const decision = formatDecisionValue(firstDefined(analysis?.decision, analysis?.result?.decision, analysis?.recommendation, analysis?.result));
  const riskLevel = firstDefined(analysis?.riskLevel, analysis?.risk_level, analysis?.result?.riskLevel, analysis?.level)?.toString().trim();

  return {
    riskScore: formatPercent(resolvedRiskValue),
    trustScore: formatPercent(resolvedTrustValue),
    riskLevel: riskLevel || classifyRiskLevel(resolvedRiskValue),
    decision: decision || deriveDecisionLabel(resolvedRiskValue),
  };
}

function firstDefined(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

function normalizePercent(value) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value === "object") {
    const nested = firstDefined(value?.score, value?.value, value?.percent, value?.percentage);
    return normalizePercent(nested);
  }
  if (typeof value === "string") {
    const cleaned = value.replace("%", "").trim();
    if (!cleaned) return null;
    const parsed = Number(cleaned);
    if (!Number.isFinite(parsed)) return null;
    return clampPercent(parsed <= 1 ? parsed * 100 : parsed);
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return clampPercent(value <= 1 ? value * 100 : value);
  }
  return null;
}

function clampPercent(value) {
  return Math.min(100, Math.max(0, Math.round(value)));
}

function formatPercent(value) {
  return value == null ? "N/A" : `${value}%`;
}

function classifyRiskLevel(riskValue) {
  if (riskValue == null) return "Chưa xác định";
  if (riskValue >= 70) return "Cao";
  if (riskValue >= 40) return "Trung bình";
  return "Thấp";
}

function deriveDecisionLabel(riskValue) {
  if (riskValue == null) return "Chưa đủ dữ liệu";
  if (riskValue >= 70) return "Nguy hiểm";
  if (riskValue >= 40) return "Cần kiểm tra thêm";
  return "Tin cậy";
}

function formatDecisionValue(value) {
  if (value === undefined || value === null || value === "") return "";
  if (typeof value === "object") {
    return (
      firstDefined(value?.label, value?.text, value?.message, value?.status, value?.decision)?.toString().trim() ||
      "Đã có quyết định phân tích"
    );
  }
  return String(value).trim();
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

function matchUserBlacklist(items = [], target = {}) {
  const normalizedTarget = normalizeJobRecord(target);
  const title = String(normalizedTarget.title || "").trim().toLowerCase();
  const companyName = String(normalizedTarget.companyName || "").trim().toLowerCase();
  const email = String(normalizedTarget.email || "").trim().toLowerCase();
  const phone = normalizePhone(normalizedTarget.phone);

  return items.filter((item) => {
    const itemTitle = String(item.title || "").trim().toLowerCase();
    const itemCompany = String(item.companyName || "").trim().toLowerCase();
    const itemEmail = String(item.email || "").trim().toLowerCase();
    const itemPhone = normalizePhone(item.phone);
    const titleMatch = itemTitle && title.includes(itemTitle);
    const companyMatch = itemCompany && companyName.includes(itemCompany);
    const emailMatch = itemEmail && email && email.includes(itemEmail);
    const phoneMatch = itemPhone && phone && phone.includes(itemPhone);
    return titleMatch || companyMatch || emailMatch || phoneMatch;
  });
}

function matchSystemBlacklist(blacklist = {}, target = {}) {
  const normalizedTarget = normalizeJobRecord(target);
  const details = [];
  const companyName = String(normalizedTarget.companyName || "").trim().toLowerCase();
  const email = String(normalizedTarget.email || "").trim().toLowerCase();
  const phone = normalizePhone(normalizedTarget.phone);

  (blacklist?.companies || []).forEach((item) => {
    const value = String(item?.name || item?.companyName || item || "").trim().toLowerCase();
    if (value && companyName.includes(value)) {
      details.push(`Công ty trùng blacklist: ${item?.name || item?.companyName || item}`);
    }
  });

  (blacklist?.emails || []).forEach((item) => {
    const value = String(item?.email || item || "").trim().toLowerCase();
    if (value && email.includes(value)) {
      details.push(`Email trùng blacklist: ${item?.email || item}`);
    }
  });

  (blacklist?.phones || []).forEach((item) => {
    const value = normalizePhone(item?.phone || item);
    if (value && phone.includes(value)) {
      details.push(`Số điện thoại trùng blacklist: ${item?.phone || item}`);
    }
  });

  return {
    hasMatch: details.length > 0,
    details,
  };
}

function normalizePhone(value) {
  return String(value || "").replace(/\D/g, "");
}

function mergeSignals(...signalGroups) {
  return [...new Set(signalGroups.flat().filter(Boolean).map((item) => String(item).trim()).filter(Boolean))];
}

function buildMissingFieldSignals(job = {}) {
  const signals = [];
  const descriptionWordCount = String(job.description || "").trim().split(/\s+/).filter(Boolean).length;

  if (descriptionWordCount > 0 && descriptionWordCount < 60) {
    signals.push("Mô tả ngắn, thiếu chi tiết công việc.");
  }
  if (!job.companyName) signals.push("Thiếu thông tin doanh nghiệp.");
  if (!job.companySize) signals.push("Thiếu quy mô công ty.");
  if (!job.companyAddress && !job.address) signals.push("Không có địa chỉ doanh nghiệp rõ ràng.");
  if (!job.requirements) signals.push("Thiếu yêu cầu công việc.");
  if (!job.email) signals.push("Thiếu email liên hệ.");
  if (!job.phone) signals.push("Thiếu số điện thoại liên hệ.");
  if (!job.jobType) signals.push("Thiếu loại hình công việc.");
  if (!job.careerLevel) signals.push("Thiếu cấp bậc công việc.");
  if (!job.experience) signals.push("Thiếu yêu cầu kinh nghiệm.");
  if (!job.salary) signals.push("Thiếu thông tin lương.");
  if (!job.submissionDeadline) signals.push("Thiếu hạn nộp hồ sơ.");
 

  return signals;
}
