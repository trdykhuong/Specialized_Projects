import { useEffect, useMemo, useState } from "react";
import { api, authStorage } from "./api";
import { sampleBatchText } from "./mockData";
import {
  AnalysisWorkspace,
  ApplicationsPanel,
  AuthRoutePage,
  BlacklistPanel,
  JobDetailPanel,
  ProfilePanel,
  SavedJobsPanel,
  StatisticsPanel,
} from "./components/AppSections";

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
  experience: "",
  careerLevel: "",
  jobType: "",
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
  const [analysisFormValidation, setAnalysisFormValidation] = useState({ errors: {}, warnings: [] });
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
  const [trainingStatus, setTrainingStatus] = useState(null);
  const isAuthRoute = routePath === "/login" || routePath === "/register";

  useEffect(() => {
    if (!successMessage) return;
    const timer = window.setTimeout(() => setSuccessMessage(""), 3200);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  useEffect(() => {
    if (!trainingStatus?.running) return undefined;
    const intervalId = window.setInterval(async () => {
      try {
        const status = await api.getTrainingStatus();
        setTrainingStatus(status);
        if (!status.running) {
          setStatusMessage(
            status.state === "completed"
              ? "Pipeline train đã hoàn tất. Backend đã nạp model mới."
              : status.message || "Pipeline train đã dừng."
          );
        }
      } catch (error) {
        window.clearInterval(intervalId);
      }
    }, 5000);
    return () => window.clearInterval(intervalId);
  }, [trainingStatus?.running]);

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
    setDetailViewMode("analysis");
    setAnalysisRequest({
      pending: true,
      context: "detail",
      error: "",
      message: "Đang phân tích tin tuyển dụng. Vui lòng chờ trong giây lát...",
    });
    try {
      const payload = mapJobToAnalysisPayload(selectedJob);
      const result = enrichAnalysisResult(await api.analyzeJob(payload), selectedJob, blacklist, userBlacklist);
      setTrainingStatus(result.training || null);
      setJobAnalysis(result);
      setDetailViewMode("analysis");
      setActivePage("detail");
      setAnalysisRequest({
        pending: false,
        context: "detail",
        error: "",
        message: "Phân tích hoàn tất. Đã cập nhật điểm rủi ro và mức độ nguy hiểm.",
      });
      setStatusMessage(buildAnalyzeStatusMessage(result.training, "Đã phân tích độ uy tín cho job đang chọn."));
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
    // Validate form
    const validation = validateAnalysisForm(analysisForm);
    setAnalysisFormValidation(validation);

    if (Object.keys(validation.errors).length > 0) {
      setAnalysisRequest({
        pending: false,
        context: "single",
        error: "Vui lòng điền đầy đủ và chính xác các trường bắt buộc. Xem chi tiết lỗi dưới form.",
        message: "",
      });
      setStatusMessage("Hãy hoàn thành form phân tích trước khi gửi.");
      return;
    }

    setAnalysisRequest({
      pending: true,
      context: "single",
      error: "",
      message: "Đang gửi dữ liệu để phân tích. Hệ thống sẽ trả về điểm rủi ro ngay khi hoàn tất...",
    });
    try {
      const result = enrichAnalysisResult(await api.analyzeJob(analysisForm), analysisForm, blacklist, userBlacklist);
      setTrainingStatus(result.training || null);
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
      setDetailViewMode("analysis");
      setActivePage("detail");
      setAnalysisFormValidation({ errors: {}, warnings: [] });
      setAnalysisRequest({
        pending: false,
        context: "single",
        error: "",
        message: "Phân tích hoàn tất. Kết quả rủi ro đã sẵn sàng.",
      });
      setStatusMessage(buildAnalyzeStatusMessage(result.training, "Đã phân tích 1 tin tuyển dụng."));
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
      const trackedJob = await prepareJobForTracking(job);
      await api.createSavedJob(buildTrackingPayload(trackedJob));
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
      const trackedJob = await prepareJobForTracking(job);
      await api.createApplication(buildTrackingPayload(trackedJob));
      await refreshUserData("Đã thêm job vào Applications.");
      setActivePage("applications");
    } catch (error) {
      setStatusMessage(error.message || "Không tạo được application.");
    }
  }

  async function prepareJobForTracking(job) {
    const draftJob = mergeTrackingDraft(job);
    const normalizedDraft = normalizeJobRecord(draftJob);

    if (normalizedDraft.id !== "" && normalizedDraft.id !== null && normalizedDraft.id !== undefined) {
      return draftJob;
    }

    const hasTrackableContent = [normalizedDraft.title, normalizedDraft.companyName, normalizedDraft.description, normalizedDraft.requirements]
      .some((value) => asTrimmedText(value));

    if (!hasTrackableContent) {
      return draftJob;
    }

    const createdJob = await api.createJob({
      ...mapJobToAnalysisPayload(draftJob),
      source: analysisFormSource === "existing" ? "existing" : "manual",
    });

    return {
      ...draftJob,
      ...createdJob,
    };
  }

  function mergeTrackingDraft(job) {
    if (job !== analysisForm) {
      return job;
    }

    if (analysisFormSource === "existing" && selectedJob) {
      return {
        ...selectedJob,
        ...analysisForm,
      };
    }

    return {
      ...analysisForm,
    };
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
            analysisFormValidation={analysisFormValidation}
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
            findCount={findCount}
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
              jobTypeOptions={JOB_TYPE_OPTIONS}
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
            normalizeJobRecord={normalizeJobRecord}
            enrichAnalysisResult={enrichAnalysisResult}
            buildAnalysisSummary={buildAnalysisSummary}
          />
        )}
      </main>
    </div>
  );
}

function validateAnalysisForm(values) {
  const errors = {};
  const warnings = [];
  const title = asTrimmedText(values.title);
  const companyName = asTrimmedText(values.companyName);
  const description = asTrimmedText(values.description);
  const requirements = asTrimmedText(values.requirements);
  const candidates = asTrimmedText(values.candidates);
  const salary = asTrimmedText(values.salary);
  const experience = asTrimmedText(values.experience);

  // Kiểm tra trường bắt buộc
  if (!title) {
    errors.title = "Tiêu đề công việc là bắt buộc.";
  } else if (title.length < 3) {
    errors.title = "Tiêu đề phải ít nhất 3 ký tự.";
  } else if (title.length > 160) {
    errors.title = "Tiêu đề không được vượt quá 160 ký tự.";
  }

  if (!companyName) {
    errors.companyName = "Tên công ty là bắt buộc.";
  } else if (companyName.length < 2) {
    errors.companyName = "Tên công ty phải ít nhất 2 ký tự.";
  } else if (companyName.length > 160) {
    errors.companyName = "Tên công ty không được vượt quá 160 ký tự.";
  }

  if (!description) {
    errors.description = "Mô tả công việc là bắt buộc để phân tích.";
  } else if (description.length < 20) {
    errors.description = "Mô tả phải ít nhất 20 ký tự (để có phân tích chính xác).";
  } else if (description.length > 2500) {
    errors.description = "Mô tả không được vượt quá 2500 ký tự.";
  }

  if (!requirements) {
    errors.requirements = "Yêu cầu công việc là bắt buộc để phân tích.";
  } else if (requirements.length < 10) {
    errors.requirements = "Yêu cầu phải ít nhất 10 ký tự (để có phân tích chính xác).";
  } else if (requirements.length > 1800) {
    errors.requirements = "Yêu cầu không được vượt quá 1800 ký tự.";
  }

  // Kiểm tra candidates nếu có
  if (candidates) {
    if (!/^\d+$/.test(candidates)) {
      errors.candidates = "Số lượng ứng viên phải là số nguyên dương.";
    }
  }

  // Cảnh báo cho các trường tiềm năng cải thiện phân tích
  if (!salary) {
    warnings.push("💡 Thêm mức lương sẽ cải thiện độ chính xác phân tích.");
  }
  if (!experience) {
    warnings.push("💡 Kinh nghiệm yêu cầu giúp lọc các công việc phù hợp.");
  }

  return { errors, warnings };
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
    title: asFormText(normalizedJob.title),
    companyName: asFormText(normalizedJob.companyName),
    description: asFormText(normalizedJob.description),
    requirements: asFormText(normalizedJob.requirements),
    benefits: asFormText(normalizedJob.benefits),
    salary: asFormText(normalizedJob.salary),
    experience: asFormText(normalizedJob.experience),
    careerLevel: asFormText(normalizedJob.careerLevel),
    jobType: asFormText(normalizedJob.jobType),
    candidates: asFormText(normalizedJob.candidates),
  };
}

function mapJobToAnalysisPayload(job = {}) {
  const normalizedJob = normalizeJobRecord(job);
  return {
    ...mapJobToAnalysisForm(job),
    candidates: Number(normalizedJob.candidates || 0),
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

function asFormText(value) {
  if (value === undefined || value === null) {
    return "";
  }
  return typeof value === "string" ? value : String(value);
}

function asTrimmedText(value) {
  return asFormText(value).trim();
}

function buildAnalyzeStatusMessage(training, fallbackMessage) {
  if (!training) return fallbackMessage;
  if (training.running) {
    return `${fallbackMessage} Pipeline train nền đã được kích hoạt từ ml_pipeline.`;
  }
  if (training.state === "completed") {
    return `${fallbackMessage} Pipeline train đã hoàn tất và model mới đã sẵn sàng.`;
  }
  if (training.state === "failed") {
    return `${fallbackMessage} Pipeline train bị lỗi, backend đang dùng model gần nhất khả dụng.`;
  }
  return fallbackMessage;
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
  if (!job.companyAddress && !job.address) signals.push("Không có địa chỉ doanh nghiệp rõ ràng.");
  if (!job.requirements) signals.push("Thiếu yêu cầu công việc.");
  if (!job.email) signals.push("Thiếu email liên hệ.");
  if (!job.phone) signals.push("Thiếu số điện thoại liên hệ.");
  if (!job.jobType) signals.push("Thiếu loại hình công việc.");
  if (!job.experience) signals.push("Thiếu yêu cầu kinh nghiệm.");
  if (!job.salary) signals.push("Thiếu thông tin lương.");
  if (!job.submissionDeadline) signals.push("Thiếu hạn nộp hồ sơ.");
 

  return signals;
}
