<template>
  <div class="ui-form-container">
    <div class="ui-card">
      <h3 class="ui-card-title">发送开关</h3>
      <div class="ui-form-group ui-checkbox-group">
        <label class="ui-switch">
          <input
            type="checkbox"
            v-model="config.SEND_EMAIL"
            true-value="true"
            false-value="false"
          />
          <span class="ui-switch-slider round"></span>
        </label>
        <span class="label-text">启用邮件发送</span>
      </div>
    </div>

    <transition name="slide-fade">
      <div v-if="emailEnabled" class="email-settings">
        <div class="ui-card">
          <h3 class="ui-card-title">发件人设置</h3>
          <div class="ui-form-row">
            <div class="ui-form-group">
              <label>SMTP 服务器</label>
              <input type="text" v-model="config.SMTP_SERVER" placeholder="smtp.example.com" />
            </div>
            <div class="ui-form-group">
              <label>端口</label>
              <input type="number" v-model="config.SMTP_PORT" placeholder="465" />
            </div>
          </div>
          <div class="ui-form-group">
            <label>发件人邮箱</label>
            <input
              type="email"
              v-model="config.SENDER_EMAIL"
              autocomplete="off"
              name="sender_email"
            />
          </div>
          <div class="ui-form-group">
            <label>邮箱密码/授权码</label>
            <div class="ui-input-wrapper">
              <input
                :type="showEmailPassword ? 'text' : 'password'"
                v-model="config.EMAIL_PASSWORD"
                autocomplete="new-password"
                name="email_password"
              />
              <button class="ui-icon-btn" @click="showEmailPassword = !showEmailPassword">
                {{ showEmailPassword ? "👁️" : "🔒" }}
              </button>
            </div>
          </div>
          <div class="ui-form-row">
            <div class="ui-form-group ui-checkbox-group">
              <label class="ui-checkbox-label">
                <input
                  type="checkbox"
                  v-model="config.USE_SSL"
                  true-value="true"
                  false-value="false"
                />
                SSL
              </label>
            </div>
            <div class="ui-form-group ui-checkbox-group">
              <label class="ui-checkbox-label">
                <input
                  type="checkbox"
                  v-model="config.USE_TLS"
                  true-value="true"
                  false-value="false"
                />
                TLS
              </label>
            </div>
          </div>
        </div>

        <div class="ui-card">
          <h3 class="ui-card-title">收件人设置</h3>
          <div class="ui-form-group">
            <label>收件人列表 (逗号分隔)</label>
            <input type="text" v-model="config.RECEIVER_EMAIL" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });

defineProps<{
  emailEnabled: boolean;
}>();

const showEmailPassword = ref(false);
</script>

<style scoped>
.email-settings {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 32px;
}
</style>
