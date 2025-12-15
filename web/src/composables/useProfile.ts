import { ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";

export function useProfile() {
  const store = useArxivStore();
  const {
    researchInterests,
    negativeInterests,
    selectedProfileName,
    userProfiles,
    selectedProfile,
    isLoading,
  } = storeToRefs(store);

  const interestsText = ref("");
  const negativeInterestsText = ref("");

  const handleProfileChange = () => {
    store.setSelectedProfile(selectedProfileName.value);
  };

  // 监听研究兴趣变化，更新文本框
  watch(
    researchInterests,
    (newInterests) => {
      interestsText.value = newInterests.join("\n");
    },
    { immediate: true }
  );

  // 监听负面偏好变化，更新文本框
  watch(
    negativeInterests,
    (newInterests) => {
      negativeInterestsText.value = newInterests.join("\n");
    },
    { immediate: true }
  );

  // 监听文本框变化，自动更新研究兴趣
  watch(interestsText, (newText) => {
    if (newText !== undefined) {
      if (newText.trim()) {
        const interests = newText.split("\n").filter((line) => line.trim());
        store.setResearchInterests(interests);
      }
    }
  });

  // 监听负面偏好文本框变化，自动更新负面偏好
  watch(negativeInterestsText, (newText) => {
    const interests = newText.trim() ? newText.split("\n").filter((line) => line.trim()) : [];
    store.setNegativeInterests(interests);
  });

  return {
    interestsText,
    negativeInterestsText,
    handleProfileChange,
    selectedProfileName,
    userProfiles,
    selectedProfile,
    isLoading,
  };
}
