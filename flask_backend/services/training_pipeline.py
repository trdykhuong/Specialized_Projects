from __future__ import annotations

import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


class TrainingPipelineManager:
    def __init__(self, project_root: Path, on_success=None):
        self.project_root = Path(project_root)
        self.pipeline_dir = self.project_root / "ml_pipeline"
        self.pipeline_script = self.pipeline_dir / "run_full_pipeline.py"
        self.log_path = self.project_root / "flask_backend" / "training_pipeline.log"
        self.on_success = on_success
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status = {
            "state": "idle",
            "running": False,
            "message": "Chưa có phiên train nào được chạy.",
            "startedAt": None,
            "finishedAt": None,
            "lastExitCode": None,
            "lastError": "",
            "runCount": 0,
            "lastTriggeredBy": "",
            "logPath": str(self.log_path),
        }

    def get_status(self):
        with self._lock:
            return dict(self._status)

    def ensure_training_started(self, triggered_by="analyze"):
        with self._lock:
            if self._status["running"]:
                status = dict(self._status)
                status["message"] = "Pipeline train đang chạy nền."
                return status

            self._status.update(
                {
                    "state": "running",
                    "running": True,
                    "message": "Đã bắt đầu train nền bằng pipeline trong ml_pipeline.",
                    "startedAt": datetime.now(timezone.utc).isoformat(),
                    "finishedAt": None,
                    "lastExitCode": None,
                    "lastError": "",
                    "runCount": int(self._status["runCount"]) + 1,
                    "lastTriggeredBy": triggered_by,
                }
            )
            self._thread = threading.Thread(target=self._run_pipeline, daemon=True)
            self._thread.start()
            return dict(self._status)

    def _run_pipeline(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc)
        try:
            command = [sys.executable, str(self.pipeline_script)]
            result = subprocess.run(
                command,
                cwd=str(self.pipeline_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            combined_output = "\n".join(part for part in [result.stdout, result.stderr] if part)
            self.log_path.write_text(combined_output, encoding="utf-8")

            with self._lock:
                self._status.update(
                    {
                        "state": "completed" if result.returncode == 0 else "failed",
                        "running": False,
                        "message": (
                            "Train hoàn tất và đã sẵn sàng nạp model mới."
                            if result.returncode == 0
                            else "Pipeline train thất bại. Xem file log để biết chi tiết."
                        ),
                        "finishedAt": datetime.now(timezone.utc).isoformat(),
                        "lastExitCode": result.returncode,
                        "lastError": "" if result.returncode == 0 else (result.stderr or result.stdout)[-4000:],
                    }
                )
            if result.returncode == 0 and callable(self.on_success):
                self.on_success()
        except Exception as error:
            self.log_path.write_text(str(error), encoding="utf-8")
            with self._lock:
                self._status.update(
                    {
                        "state": "failed",
                        "running": False,
                        "message": "Pipeline train lỗi khi khởi chạy.",
                        "finishedAt": datetime.now(timezone.utc).isoformat(),
                        "lastExitCode": -1,
                        "lastError": str(error),
                    }
                )
        finally:
            duration = (datetime.now(timezone.utc) - started_at).total_seconds()
            with self._lock:
                self._status["durationSeconds"] = round(duration, 2)
