import { ref } from "vue";

export function useToast() {
  const message = ref<{ text: string; type: "success" | "error" }>({
    text: "",
    type: "success",
  });

  const showMessage = (text: string, type: "success" | "error" = "success") => {
    message.value = { text, type };
    setTimeout(() => {
      message.value.text = "";
    }, 3000);
  };

  return {
    message,
    showMessage,
  };
}
