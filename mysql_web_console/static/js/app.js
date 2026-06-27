const { createApp, ref, computed, nextTick } = Vue;

createApp({
  setup() {
    const loginView = ref(true);
    const isLoginMode = ref(false);
    const loginHost = ref("127.0.0.1");
    const loginPort = ref("3306");
    const loginUser = ref("root");
    const loginPassword = ref("");
    const loginDb = ref("");
    const rememberLogin = ref(false);
    const showPassword = ref(false);
    const loginLoading = ref(false);
    const loginError = ref("");
    let authToken = null;

    function getToken() {
      if (authToken) return authToken;
      try {
        const t = localStorage.getItem("mwc_token");
        if (t) {
          authToken = t;
          return t;
        }
      } catch (e) {}
      return null;
    }

    function setToken(token) {
      authToken = token;
      try {
        localStorage.setItem("mwc_token", token);
      } catch (e) {}
    }

    function clearToken() {
      authToken = null;
      try {
        localStorage.removeItem("mwc_token");
      } catch (e) {}
    }

    function loadCredentials() {
      try {
        const raw = localStorage.getItem("mwc_credentials");
        if (!raw) return;
        const c = JSON.parse(raw);
        loginHost.value = c.host || "127.0.0.1";
        loginPort.value = c.port || "3306";
        loginUser.value = c.user || "root";
        loginPassword.value = c.password || "";
        loginDb.value = c.db || "";
        rememberLogin.value = true;
      } catch (e) {}
    }

    function saveCredentials() {
      try {
        localStorage.setItem(
          "mwc_credentials",
          JSON.stringify({
            host: loginHost.value,
            port: loginPort.value,
            user: loginUser.value,
            password: loginPassword.value,
            db: loginDb.value,
          }),
        );
      } catch (e) {}
    }

    function clearCredentials() {
      try {
        localStorage.removeItem("mwc_credentials");
      } catch (e) {}
    }

    async function authedFetch(url, options = {}) {
      const token = getToken();
      if (token) {
        if (!options.headers) options.headers = {};
        options.headers["Authorization"] = "Bearer " + token;
      }
      const res = await fetch(url, options);
      if (res.status === 401 && isLoginMode.value) {
        clearToken();
        loginView.value = true;
        try {
          const errData = await res.clone().json();
          loginError.value = errData.detail || "会话已过期，请重新登录";
        } catch (e) {
          loginError.value = "会话已过期，请重新登录";
        }
      }
      return res;
    }

    async function checkAuth() {
      try {
        const res = await fetch("/api/auth-status");
        const data = await res.json();
        isLoginMode.value = data.require_login;
        if (!data.require_login) {
          loginView.value = false;
          loadFavorites();
          fetchDbInfo();
          loadTables();
          return;
        }
        if (data.authenticated && getToken()) {
          loginView.value = false;
          loadFavorites();
          fetchDbInfo();
          loadTables();
        } else {
          loadCredentials();
          loginView.value = true;
        }
      } catch (e) {
        loginView.value = false;
        loadFavorites();
        fetchDbInfo();
        loadTables();
      }
    }

    checkAuth();

    async function doLogin() {
      loginError.value = "";
      loginLoading.value = true;
      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            host: loginHost.value || "127.0.0.1",
            port: parseInt(loginPort.value) || 3306,
            user: loginUser.value || "root",
            password: loginPassword.value,
            db: loginDb.value,
          }),
        });
        const data = await res.json();
        if (data.success) {
          setToken(data.token);
          if (rememberLogin.value) {
            saveCredentials();
          } else {
            clearCredentials();
          }
          loginView.value = false;
          fetchDbInfo();
          loadTables();
          loadFavorites();
        } else {
          loginError.value = data.message || "连接失败";
        }
      } catch (e) {
        loginError.value = "网络错误: " + e.message;
      } finally {
        loginLoading.value = false;
      }
    }

    async function doLogout() {
      try {
        const token = getToken();
        const headers = {};
        if (token) headers["Authorization"] = "Bearer " + token;
        await fetch("/api/logout", { method: "POST", headers });
      } catch (e) {}
      clearToken();
      if (!rememberLogin.value) {
        clearCredentials();
      }
      loginHost.value = "127.0.0.1";
      loginPort.value = "3306";
      loginUser.value = "root";
      loginPassword.value = "";
      loginDb.value = "";
      rememberLogin.value = false;
      loginView.value = true;
      loginError.value = "";
      currentDb.value = null;
      tableList.value = [];
      result.value = null;
      procList.value = [];
      procLoaded.value = false;
    }

    const sql = ref("");
    const loading = ref(false);
    const result = ref(null);
    const currentDb = ref(null);

    const favorites = ref([]);
    const favSearch = ref("");
    const favLoading = ref(false);
    const favToast = ref(null);
    const favNameDialog = ref(false);
    const favNameInput = ref("");
    const favPendingSql = ref("");
    const favValidationError = ref("");

    const procList = ref([]);
    const procSearch = ref("");
    const procLoading = ref(false);
    const procLoaded = ref(false);

    const pickerView = ref(false);

    const randMax = ref("");
    const randResult = ref(null);
    const randError = ref("");
    const randOpen = ref(true);

    const copyToast = ref("");

    const tableList = ref([]);
    const tablesLoading = ref(false);
    const tableListView = ref("list");
    const selectedTable = ref("");
    const tableDetailColumns = ref([]);
    const tableDetailRows = ref([]);
    const tableDetailLoading = ref(false);

    const filteredProcList = computed(() => {
      const keyword = procSearch.value.trim().toLowerCase();
      if (!keyword) return procList.value;
      return procList.value.filter((n) => n.toLowerCase().includes(keyword));
    });

    const filteredFavorites = computed(() => {
      const keyword = favSearch.value.trim().toLowerCase();
      if (!keyword) return favorites.value;
      return favorites.value.filter(
        (f) =>
          f.name.toLowerCase().includes(keyword) ||
          f.sql.toLowerCase().includes(keyword),
      );
    });

    const pickerFavFlex = computed(() => {
      const favCount = filteredFavorites.value.length;
      const procCount = filteredProcList.value.length;
      if (favCount === 0 && procCount === 0) return 1;
      return Math.max(favCount, 3);
    });

    const pickerProcFlex = computed(() => {
      const favCount = filteredFavorites.value.length;
      const procCount = filteredProcList.value.length;
      if (favCount === 0 && procCount === 0) return 1;
      return Math.max(procCount, 3);
    });

    async function loadTables() {
      tablesLoading.value = true;
      try {
        const res = await authedFetch("/api/tables");
        const data = await res.json();
        tableList.value = data.tables || [];
      } catch (e) {
        tableList.value = [];
      } finally {
        tablesLoading.value = false;
      }
    }

    async function openTableDetail(tableName) {
      selectedTable.value = tableName;
      tableListView.value = "detail";
      tableDetailLoading.value = true;
      tableDetailColumns.value = [];
      tableDetailRows.value = [];
      try {
        const res = await authedFetch(
          "/api/tables/" + encodeURIComponent(tableName) + "/desc",
        );
        const data = await res.json();
        if (data.success) {
          tableDetailColumns.value = data.columns || [];
          tableDetailRows.value = data.rows || [];
        }
      } catch (e) {
        tableDetailColumns.value = [];
        tableDetailRows.value = [];
      } finally {
        tableDetailLoading.value = false;
      }
    }

    function focusTextarea() {
      const ta = document.querySelector("textarea");
      if (!ta) return;
      ta.focus();
      const idx = sql.value.indexOf("<");
      if (idx >= 0) {
        requestAnimationFrame(() => {
          ta.selectionStart = idx;
          ta.selectionEnd = sql.value.indexOf(">", idx) + 1;
        });
      }
    }

    function fillSelect() {
      sql.value = "SELECT * FROM `" + selectedTable.value + "` WHERE <条件>;";
      focusTextarea();
    }

    function fillInsert() {
      const cols = tableDetailRows.value.map((r) => "`" + r[0] + "`");
      const vals = tableDetailRows.value.map(() => "<值>");
      sql.value =
        "INSERT INTO `" +
        selectedTable.value +
        "` (" +
        cols.join(", ") +
        ")\nVALUES (" +
        vals.join(", ") +
        ");";
      focusTextarea();
    }

    function fillUpdate() {
      const sets = tableDetailRows.value.map((r) => "`" + r[0] + "` = <值>");
      sql.value =
        "UPDATE `" +
        selectedTable.value +
        "` SET " +
        sets.join(", ") +
        "\nWHERE <条件>;";
      focusTextarea();
    }

    function fillDelete() {
      sql.value = "DELETE FROM `" + selectedTable.value + "` WHERE <条件>;";
      focusTextarea();
    }

    async function loadFavorites() {
      try {
        const res = await authedFetch("/api/favorites");
        const data = await res.json();
        favorites.value = data.favorites || [];
      } catch (e) {
        favorites.value = [];
      }
    }

    async function removeFavorite(id) {
      try {
        await authedFetch("/api/favorites/" + id, { method: "DELETE" });
        favorites.value = favorites.value.filter((f) => f.id !== id);
      } catch (e) {}
    }

    function showFavToast(text, type) {
      favToast.value = { text, type };
      setTimeout(() => {
        favToast.value = null;
      }, 2000);
    }

    async function handleFavorite() {
      const sqlStr = sql.value.trim();
      if (!sqlStr) {
        showFavToast("请先输入 SQL 语句", "warn");
        return;
      }
      favPendingSql.value = sqlStr;
      favNameInput.value = "";
      favValidationError.value = "";
      favNameDialog.value = true;
      nextTick(() => {
        const input =
          document.querySelector('[ref="favNameInputRef"]') ||
          document.querySelector(
            '.bg-gray-800 input[placeholder="输入收藏命名..."]',
          );
        if (input) input.focus();
      });
    }

    async function confirmFavorite(force = false) {
      const name = favNameInput.value.trim();
      if (!name) return;
      favLoading.value = true;
      try {
        const res = await authedFetch("/api/favorites", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            sql: favPendingSql.value,
            force: force,
          }),
        });
        const data = await res.json();
        if (data.success) {
          favorites.value.unshift(data.favorite);
          favNameDialog.value = false;
          favValidationError.value = "";
          showFavToast("⭐ 收藏成功", "success");
        } else if (data.validation_error) {
          favValidationError.value = data.message || "SQL 校验未通过";
        } else {
          showFavToast(data.message || "收藏失败", "error");
        }
      } catch (e) {
        showFavToast("收藏请求失败", "error");
      } finally {
        favLoading.value = false;
      }
    }

    async function fetchDbInfo() {
      try {
        const res = await authedFetch("/api/info");
        const data = await res.json();
        currentDb.value = data.database || null;
      } catch (e) {
        currentDb.value = null;
      }
    }

    async function openPicker() {
      pickerView.value = true;
      if (!procLoaded.value) {
        await loadProcedures();
      }
    }

    function closePicker() {
      pickerView.value = false;
      favSearch.value = "";
      procSearch.value = "";
    }

    async function loadProcedures() {
      procLoading.value = true;
      try {
        const res = await authedFetch("/api/procedures");
        const data = await res.json();
        procList.value = data.procedures || [];
        procLoaded.value = true;
      } catch (e) {
        procList.value = [];
      } finally {
        procLoading.value = false;
      }
    }

    async function selectProcedure(name) {
      const ta = document.querySelector("textarea");
      if (ta) ta.focus();
      try {
        const res = await authedFetch(
          "/api/procedures/" + encodeURIComponent(name) + "/params",
        );
        const data = await res.json();
        const params = data.params || [];
        if (params.length === 0) {
          sql.value = "CALL " + name + "();";
        } else {
          const args = params.map((p) => {
            if (p.direction === "OUT") return "@" + p.name + "_auto";
            if (p.direction === "INOUT") return "<@" + p.name + "_auto>";
            return "<" + p.name + ">";
          });
          sql.value = "CALL " + name + "(" + args.join(", ") + ");";
        }
      } catch (e) {
        sql.value = "CALL " + name + "();";
      }
      procSearch.value = "";
      if (sql.value.includes("<") && ta) {
        requestAnimationFrame(() => {
          const idx = sql.value.indexOf("<");
          ta.selectionStart = idx;
          ta.selectionEnd = sql.value.indexOf(">", idx) + 1;
        });
      } else if (ta) {
        ta.blur();
      }
    }

    async function selectProcedureFromPicker(name) {
      await selectProcedure(name);
      closePicker();
    }

    function generateRandom() {
      randResult.value = null;
      randError.value = "";
      const val = String(randMax.value).trim();
      if (!val || val === "") {
        randError.value = "请输入一个整数";
        return;
      }
      const num = Number(val);
      if (!Number.isInteger(num)) {
        randError.value = "请输入有效的整数";
        return;
      }
      if (num <= 1) {
        randError.value = "请输入大于1的整数";
        return;
      }
      randResult.value = Math.floor(Math.random() * num) + 1;
    }

    async function executeSql() {
      if (!sql.value.trim() || loading.value) return;

      loading.value = true;
      result.value = null;

      try {
        const response = await authedFetch("/api/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sql: sql.value.trim() }),
        });
        const data = await response.json();
        result.value = data;

        if (data.success) {
          loadTables();
          tableListView.value = "list";
          if (sql.value.trim().toUpperCase().startsWith("USE ")) {
            fetchDbInfo();
          }
        }
      } catch (err) {
        result.value = {
          success: false,
          message: "网络错误: " + err.message,
          duration_ms: 0.0,
          columns: [],
          rows: [],
          affected_rows: 0,
          out_params: [],
        };
      } finally {
        loading.value = false;
        nextTick(() => {
          const el = document.getElementById("output-area");
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      }
    }

    function insertTab() {
      const ta = document.querySelector("textarea");
      if (!ta) return;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const val = sql.value;
      sql.value = val.substring(0, start) + "\t" + val.substring(end);
      nextTick(() => {
        ta.selectionStart = ta.selectionEnd = start + 1;
        ta.focus();
      });
    }

    function insertQuote() {
      const ta = document.querySelector("textarea");
      if (!ta) return;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const val = sql.value;
      const inserted = "' '";
      sql.value = val.substring(0, start) + inserted + val.substring(end);
      nextTick(() => {
        ta.selectionStart = start + 1;
        ta.selectionEnd = start + 2;
        ta.focus();
      });
    }

    function clearSql() {
      sql.value = "";
    }

    function escapeCsvCell(cell) {
      if (cell === null || cell === undefined) return "";
      const str = String(cell);
      if (
        str.includes(",") ||
        str.includes('"') ||
        str.includes("\n") ||
        str.includes("\r")
      ) {
        return '"' + str.replace(/"/g, '""') + '"';
      }
      return str;
    }

    function fallbackCopyText(text) {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      ta.style.top = "-9999px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.setSelectionRange(0, ta.value.length);
      let ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (e) {
        ok = false;
      }
      document.body.removeChild(ta);
      return ok;
    }

    function copyAsMarkdown(columns, rows) {
      const header = "| " + columns.join(" | ") + " |";
      const separator = "| " + columns.map(() => "---").join(" | ") + " |";
      const body = rows
        .map(
          (row) =>
            "| " +
            row
              .map((cell) => (cell === null ? "NULL" : String(cell)))
              .join(" | ") +
            " |",
        )
        .join("\n");
      const md = header + "\n" + separator + "\n" + body;
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard
          .writeText(md)
          .then(() => {
            copyToast.value = "已复制到剪贴板";
            setTimeout(() => {
              copyToast.value = "";
            }, 1500);
          })
          .catch(() => {
            const ok = fallbackCopyText(md);
            copyToast.value = ok ? "已复制到剪贴板" : "复制失败";
            setTimeout(() => {
              copyToast.value = "";
            }, 1500);
          });
      } else {
        const ok = fallbackCopyText(md);
        copyToast.value = ok ? "已复制到剪贴板" : "复制失败";
        setTimeout(() => {
          copyToast.value = "";
        }, 1500);
      }
    }

    function downloadCsv(columns, rows, filename) {
      const header = columns.map(escapeCsvCell).join(",");
      const body = rows
        .map((row) => row.map(escapeCsvCell).join(","))
        .join("\n");
      const csv = "\uFEFF" + header + "\n" + body;
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }

    function onKeydown(e) {
      if (e.key === "Tab") {
        e.preventDefault();
        insertTab();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        executeSql();
      }
    }

    return {
      loginView,
      isLoginMode,
      loginHost,
      loginPort,
      loginUser,
      loginPassword,
      loginDb,
      rememberLogin,
      showPassword,
      loginLoading,
      loginError,
      doLogin,
      doLogout,
      sql,
      loading,
      result,
      currentDb,
      favorites,
      favSearch,
      favLoading,
      favToast,
      favNameDialog,
      favNameInput,
      favPendingSql,
      favValidationError,
      filteredFavorites,
      pickerView,
      pickerFavFlex,
      pickerProcFlex,
      openPicker,
      closePicker,
      handleFavorite,
      confirmFavorite,
      removeFavorite,
      insertTab,
      insertQuote,
      executeSql,
      onKeydown,
      procList,
      procSearch,
      procLoading,
      filteredProcList,
      selectProcedure,
      selectProcedureFromPicker,
      randMax,
      randResult,
      randError,
      randOpen,
      generateRandom,
      clearSql,
      copyAsMarkdown,
      downloadCsv,
      copyToast,
      tableList,
      tablesLoading,
      tableListView,
      selectedTable,
      tableDetailColumns,
      tableDetailRows,
      tableDetailLoading,
      openTableDetail,
      fillSelect,
      fillInsert,
      fillUpdate,
      fillDelete,
    };
  },
}).mount("#app");
