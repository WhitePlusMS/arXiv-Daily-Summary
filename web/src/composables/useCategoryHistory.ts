import { ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { UserProfile } from "@/types";

export function useCategoryHistory() {
  const store = useArxivStore();
  const { userProfiles, isLoading } = storeToRefs(store);

  // State
  const stats = ref<{ total_records?: number; unique_users?: number } | null>(null);
  const managementCollapsed = ref(false);
  const searchTerm = ref("");
  const selectedIndices = ref<Set<number>>(new Set());
  const editModes = ref<Set<number>>(new Set());
  const editDrafts = ref<
    Record<
      number,
      { username: string; category_id: string; user_input: string; negative_query: string }
    >
  >({});

  // Computed
  const filteredProfiles = computed(() => {
    const term = searchTerm.value.trim().toLowerCase();
    const reversedProfiles = [...userProfiles.value].reverse();
    if (!term) return reversedProfiles;
    return reversedProfiles.filter(
      (item) =>
        (item.username || "").toLowerCase().includes(term) ||
        (item.user_input || "").toLowerCase().includes(term) ||
        (item.negative_query || "").toLowerCase().includes(term) ||
        (item.category_id || "").toLowerCase().includes(term)
    );
  });

  // Methods
  const toggleManagementCollapse = () => {
    managementCollapsed.value = !managementCollapsed.value;
    try {
      localStorage.setItem("matcher_management_collapsed", managementCollapsed.value ? "1" : "0");
    } catch {}
  };

  const initManagementCollapse = () => {
    try {
      const s2 = localStorage.getItem("matcher_management_collapsed");
      if (s2 === "1") managementCollapsed.value = true;
      else if (s2 === "0") managementCollapsed.value = false;
    } catch {}
  };

  const refreshData = async () => {
    store.setLoading(true);
    store.clearError();
    try {
      const configResponse = await api.getConfig();
      if (configResponse.success && configResponse.data) {
        store.setConfig(configResponse.data);
      }
      const res = await api.getMatcherDataOrProfiles();
      if (res.success && res.data) {
        store.setUserProfiles(res.data as UserProfile[]);
        stats.value =
          (res as { stats?: { total_records?: number; unique_users?: number } }).stats || null;
      } else {
        stats.value = null;
      }
    } catch (err) {
      store.setError("刷新数据时发生错误");
      console.error("刷新数据错误:", err);
    } finally {
      store.setLoading(false);
    }
  };

  const selectAll = () => {
    selectedIndices.value = new Set(filteredProfiles.value.map((_, i) => i));
  };

  const clearSelection = () => {
    selectedIndices.value.clear();
  };

  const toggleSelection = (i: number, checked: boolean) => {
    if (checked) selectedIndices.value.add(i);
    else selectedIndices.value.delete(i);
  };

  const batchDelete = () => {
    if (selectedIndices.value.size === 0) return;
    const indices = Array.from(selectedIndices.value).map((i) => {
      const item = filteredProfiles.value[i];
      return item ? userProfiles.value.indexOf(item) : -1;
    });
    const valid = indices.filter((i) => i >= 0);
    if (valid.length === 0) return;
    store.setLoading(true);
    api
      .batchDeleteMatcherRecords({ indices: valid })
      .then(async (resp) => {
        if (resp.success) {
          selectedIndices.value.clear();
          await refreshData();
        } else {
          store.setError("批量删除失败");
        }
      })
      .catch((err) => {
        store.setError("批量删除时发生错误");
        console.error("批量删除错误:", err);
      })
      .finally(() => {
        store.setLoading(false);
      });
  };

  const exportJSON = () => {
    const exportData = filteredProfiles.value;
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `user_categories_${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:T]/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleEdit = (i: number) => {
    const item = filteredProfiles.value[i];
    if (!item) return;
    if (editModes.value.has(i)) {
      // Save logic
      const originalIndex = userProfiles.value.indexOf(item);
      if (originalIndex < 0) return;
      const draft = editDrafts.value[i];
      if (!draft) return;
      store.setLoading(true);
      api
        .updateMatcherRecord({
          index: originalIndex,
          username: draft.username || "",
          category_id: draft.category_id || "",
          user_input: draft.user_input || "",
          negative_query: draft.negative_query || "",
        })
        .then(async (resp) => {
          if (resp.success) {
            editModes.value.delete(i);
            delete editDrafts.value[i];
            await refreshData();
          } else {
            store.setError("更新记录失败");
          }
        })
        .catch((err) => {
          store.setError("更新记录时发生错误");
          console.error("更新记录错误:", err);
        })
        .finally(() => {
          store.setLoading(false);
        });
    } else {
      // Enter edit mode
      editModes.value.add(i);
      editDrafts.value[i] = {
        username: item.username || "",
        category_id: item.category_id || "",
        user_input: item.user_input || "",
        negative_query: item.negative_query || "",
      };
    }
  };

  const cancelEdit = (i: number) => {
    editModes.value.delete(i);
    delete editDrafts.value[i];
  };

  const deleteRecord = (i: number) => {
    const item = filteredProfiles.value[i];
    if (!item) return;
    const originalIndex = userProfiles.value.indexOf(item);
    if (originalIndex < 0) return;
    if (!confirm("确认删除该记录？此操作不可撤销。")) return;
    store.setLoading(true);
    api
      .deleteMatcherRecord({ index: originalIndex })
      .then(async (resp) => {
        if (resp.success) {
          await refreshData();
        } else {
          store.setError("删除记录失败");
        }
      })
      .catch((err) => {
        store.setError("删除记录时发生错误");
        console.error("删除记录错误:", err);
      })
      .finally(() => {
        store.setLoading(false);
      });
  };

  const updateDraftField = (index: number, field: string, value: string) => {
    if (editDrafts.value[index]) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (editDrafts.value[index] as any)[field] = value;
    }
  };

  return {
    stats,
    managementCollapsed,
    searchTerm,
    selectedIndices,
    editModes,
    editDrafts,
    filteredProfiles,
    isLoading,
    toggleManagementCollapse,
    initManagementCollapse,
    refreshData,
    selectAll,
    clearSelection,
    toggleSelection,
    batchDelete,
    exportJSON,
    toggleEdit,
    cancelEdit,
    deleteRecord,
    updateDraftField,
  };
}
