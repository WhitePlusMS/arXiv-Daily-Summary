import { ref, onMounted, onUnmounted } from "vue";

export function useTime() {
  const localTime = ref("");
  const arxivTime = ref("");
  const localTimezone = ref("");
  const arxivTimezone = ref("");
  let timer: number | null = null;

  const updateTime = () => {
    const now = new Date();

    // 本地时间
    localTime.value = now.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    // 获取本地时区
    const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    localTimezone.value = localTz;

    // ArXiv时间 (US/Eastern)
    const arxivDate = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
    arxivTime.value = arxivDate.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    // 判断是否为夏令时
    const january = new Date(now.getFullYear(), 0, 1);
    const july = new Date(now.getFullYear(), 6, 1);
    const stdOffset = Math.max(january.getTimezoneOffset(), july.getTimezoneOffset());
    const isDST = now.getTimezoneOffset() < stdOffset;
    arxivTimezone.value = isDST ? "EDT" : "EST";
  };

  onMounted(() => {
    updateTime();
    timer = setInterval(updateTime, 1000) as unknown as number;
  });

  onUnmounted(() => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  });

  return {
    localTime,
    arxivTime,
    localTimezone,
    arxivTimezone,
  };
}
