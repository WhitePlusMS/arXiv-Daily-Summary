/**
 * 进度服务 - 用于轮询任务进度
 */

import type { ProgressData } from "@/types";

export type ProgressCallback = (progress: ProgressData) => void;
export type CompleteCallback = (progress: ProgressData) => void;
export type ErrorCallback = (error: string) => void;

class ProgressService {
  private pollingIntervals: Map<string, number> = new Map();
  private BASE_URL = import.meta.env.VITE_API_BASE_URL || "" || "http://localhost:8000";

  /**
   * 开始轮询任务进度
   * @param taskId 任务ID
   * @param onUpdate 进度更新回调
   * @param onComplete 任务完成回调
   * @param onError 错误回调
   * @param intervalMs 轮询间隔（毫秒），默认1500ms
   */
  startPolling(
    taskId: string,
    onUpdate: ProgressCallback,
    onComplete: CompleteCallback,
    onError?: ErrorCallback,
    intervalMs: number = 1500
  ): void {
    // 如果已经在轮询这个任务，先停止
    this.stopPolling(taskId);

    // 立即执行一次查询
    this.fetchProgress(taskId, onUpdate, onComplete, onError);

    // 设置定时轮询
    const intervalId = window.setInterval(() => {
      this.fetchProgress(taskId, onUpdate, onComplete, onError);
    }, intervalMs);

    this.pollingIntervals.set(taskId, intervalId);
  }

  /**
   * 停止轮询任务进度
   * @param taskId 任务ID
   */
  stopPolling(taskId: string): void {
    const intervalId = this.pollingIntervals.get(taskId);
    if (intervalId) {
      window.clearInterval(intervalId);
      this.pollingIntervals.delete(taskId);
    }
  }

  /**
   * 停止所有轮询
   */
  stopAllPolling(): void {
    this.pollingIntervals.forEach((intervalId) => {
      window.clearInterval(intervalId);
    });
    this.pollingIntervals.clear();
  }

  /**
   * 获取任务进度（单次查询）
   * @param taskId 任务ID
   * @param onUpdate 进度更新回调
   * @param onComplete 任务完成回调
   * @param onError 错误回调
   */
  private async fetchProgress(
    taskId: string,
    onUpdate: ProgressCallback,
    onComplete: CompleteCallback,
    onError?: ErrorCallback
  ): Promise<void> {
    try {
      const response = await fetch(`${this.BASE_URL}/api/tasks/${taskId}/progress`);

      if (!response.ok) {
        if (response.status === 404) {
          // 任务不存在或已过期
          this.stopPolling(taskId);
          if (onError) {
            onError("任务不存在或已过期");
          }
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        const progress: ProgressData = result.data;

        // 调用更新回调
        onUpdate(progress);

        // 检查任务是否完成
        if (progress.status === "completed") {
          this.stopPolling(taskId);
          onComplete(progress);
        } else if (progress.status === "failed") {
          this.stopPolling(taskId);
          if (onError) {
            onError(progress.error || "任务执行失败");
          }
        }
      } else {
        throw new Error(result.message || "获取进度失败");
      }
    } catch (error) {
      // 网络错误或其他异常
      console.error("获取进度失败:", error);
      if (onError) {
        const errorMessage = error instanceof Error ? error.message : "获取进度失败";
        onError(errorMessage);
      }
      // 不自动停止轮询，让用户决定
    }
  }

  /**
   * 删除任务
   * @param taskId 任务ID
   */
  async deleteTask(taskId: string): Promise<boolean> {
    try {
      // 先停止轮询
      this.stopPolling(taskId);

      const response = await fetch(`${this.BASE_URL}/api/tasks/${taskId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error("删除任务失败:", error);
      return false;
    }
  }
}

// 导出单例实例
export const progressService = new ProgressService();

// 导出类（用于类型）
export default ProgressService;
