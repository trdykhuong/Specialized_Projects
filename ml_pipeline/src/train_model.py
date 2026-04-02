import os
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve,
                             accuracy_score, precision_score, recall_score, f1_score)
from scipy.sparse import hstack
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import warnings
warnings.filterwarnings('ignore')

BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
DATA_DIR  = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# ============================================================
# DANH SÁCH FEATURES — nguồn thật duy nhất
# Thêm/bớt feature ở đây, tất cả các hàm đều dùng list này.
# ============================================================

NUMERIC_FEATURES = [
    # ── Text features ──────────────────────────────────────
    'text_length', 'char_length', 'avg_word_length',
    'uppercase_ratio', 'exclamation_count', 'number_count',
    'vocab_diversity', 'scam_keyword_count', 'positive_keyword_count',
    'max_word_repetition',

    # ── Salary features ────────────────────────────────────
    'salary_missing', 'salary_negotiable', 'salary_avg',
    'salary_range_width', 'salary_suspiciously_high', 'salary_too_low',

    # ── Company size / overview (từ advanced_features) ─────
    'company_size_missing', 'company_size_value', 'is_small_company',
    'company_overview_length', 'company_overview_missing',

    # ── Requirement features ───────────────────────────────
    'no_experience_required', 'experience_years',
    'num_candidates', 'mass_recruitment',
    'requirements_length', 'requirements_missing',

    # ── Company lookup features (từ enrich_company_features) ─
    'company_name_is_direct',   # 1 nếu tên lấy từ cột, 0 nếu extract từ text
    'company_found',            # 1 nếu tìm được MST trên masothue
    'company_verified',         # 1 nếu crawl masothue thành công
    'company_active',           # 1 nếu đang hoạt động
    'company_closed',           # 1 nếu đã ngừng hoạt động
    'company_unknown',          # 1 nếu không rõ trạng thái
    'company_age_months',       # số tháng tuổi công ty
    'company_match_score',      # độ tin cậy khi match tên → MST
    'company_is_branch',        # 1 nếu là chi nhánh

    # ── Reputation features — keyword-based ────────────────
    'reputation_found',
    'reputation_negative_hits',
    'reputation_avg_risk',
    'reputation_max_risk',
    'reputation_score',

    # ── Reputation features — BERT (tuỳ chọn, chỉ có nếu chạy --use-dl) ──
    'dl_rep_score',
    'dl_rep_avg',
    'dl_rep_max',
    'dl_rep_high_ratio',
]


class EnsembleJobClassifier:

    def __init__(self, use_high_confidence_only=True, confidence_threshold=0.7):
        self.use_high_confidence  = use_high_confidence_only
        self.confidence_threshold = confidence_threshold

        self.tfidf = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            min_df=3,
            max_df=0.8
        )
        self.scaler = StandardScaler()

        self.models = {
            'LogisticRegression': LogisticRegression(
                max_iter=1000, class_weight='balanced', C=0.5, random_state=42
            ),
            'RandomForest': RandomForestClassifier(
                n_estimators=200, max_depth=15,
                min_samples_split=10, min_samples_leaf=4,
                class_weight='balanced', random_state=42, n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=150, max_depth=5, learning_rate=0.1, random_state=42
            ),
            'XGBoost': XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                scale_pos_weight=1.5, random_state=42,
                use_label_encoder=False, eval_metric='logloss'
            ),
            'LightGBM': LGBMClassifier(
                n_estimators=200, max_depth=7, learning_rate=0.1,
                class_weight='balanced', random_state=42, verbose=-1
            ),
        }

        self.voting_clf    = None
        self.best_model    = None
        self.best_model_name = None
        self.used_features = None   # lưu lại features thực sự dùng để predict sau này

    # ────────────────────────────────────────────────────────
    def load_and_prepare_data(self):
        print("Đang load dữ liệu...")

        # Ưu tiên dùng file đã có company features
        for fname in ["../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv", "../data/JOB_DATA_HIGH_CONFIDENCE_KHOA.csv"]:
            path = os.path.join(DATA_DIR, fname)
            if os.path.exists(path):
                df = pd.read_csv(path, encoding="utf-8-sig")
                print(f"Đọc từ: {fname} ({len(df)} mẫu)")
                break
        else:
            raise FileNotFoundError(
                "Không tìm thấy JOB_DATA_IMPROVED_LABELS_KHOA.csv. "
                "Hãy chạy labeling.py trước."
            )

        if self.use_high_confidence:
            original = len(df)
            df = df[df['confidence'] >= self.confidence_threshold]
            print(f"Lọc high-confidence: {original} → {len(df)} mẫu")

        # Báo cáo company features có trong data
        company_cols = [c for c in df.columns if c in NUMERIC_FEATURES
                        and c.startswith(('company_', 'reputation_', 'dl_rep'))]
        print(f"Company features có trong data: {company_cols}")

        return df

    # ────────────────────────────────────────────────────────
    def prepare_features(self, df, fit=True):
        """Chuẩn bị feature matrix. Tự động bỏ qua cột không có trong data."""

        # 1. TF-IDF
        X_text_raw = df['FULL_TEXT'].fillna("")
        if fit:
            X_text = self.tfidf.fit_transform(X_text_raw)
        else:
            X_text = self.tfidf.transform(X_text_raw)

        # 2. Numeric — chỉ lấy cột thực sự có trong df
        if fit:
            available = [f for f in NUMERIC_FEATURES if f in df.columns]
            self.used_features = available   # lưu lại thứ tự cho lần predict
            print(f"Numeric features: {len(available)} / {len(NUMERIC_FEATURES)} "
                  f"(thiếu: {set(NUMERIC_FEATURES) - set(available)})")
        else:
            available = self.used_features   # dùng đúng thứ tự lúc train

        X_num = df[available].fillna(0)
        if fit:
            X_num_scaled = self.scaler.fit_transform(X_num)
        else:
            X_num_scaled = self.scaler.transform(X_num)

        return hstack([X_text, X_num_scaled])

    # ────────────────────────────────────────────────────────
    def train_and_evaluate_models(self, X_train, X_test, y_train, y_test):
        results = {}
        print("\n" + "=" * 80)
        print("TRAINING VÀ ĐÁNH GIÁ CÁC MODELS")
        print("=" * 80)

        for name, model in self.models.items():
            print(f"\n[{name}]")
            print("-" * 40)
            model.fit(X_train, y_train)
            y_pred  = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            acc  = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec  = recall_score(y_test, y_pred, zero_division=0)
            f1   = f1_score(y_test, y_pred, zero_division=0)
            auc  = roc_auc_score(y_test, y_proba)

            results[name] = dict(model=model, accuracy=acc, precision=prec,
                                 recall=rec, f1=f1, auc=auc,
                                 y_pred=y_pred, y_proba=y_proba)
            print(f"Accuracy : {acc:.4f}")
            print(f"Precision: {prec:.4f}")
            print(f"Recall   : {rec:.4f}")
            print(f"F1-Score : {f1:.4f}")
            print(f"AUC-ROC  : {auc:.4f}")

        return results

    # ────────────────────────────────────────────────────────
    def create_voting_ensemble(self, results):
        sorted_models = sorted(results.items(), key=lambda x: x[1]['f1'], reverse=True)
        top_3 = sorted_models[:3]
        print("\nTop 3 models cho Voting Ensemble:")
        for name, r in top_3:
            print(f"  {name}: F1={r['f1']:.4f}, AUC={r['auc']:.4f}")

        self.voting_clf = VotingClassifier(
            estimators=[(n, r['model']) for n, r in top_3],
            voting='soft',
            weights=[3, 2, 1]
        )
        return self.voting_clf

    # ────────────────────────────────────────────────────────
    def cross_validation_evaluation(self, X, y):
        print("\n" + "=" * 80)
        print("CROSS-VALIDATION (5-FOLD)")
        print("=" * 80)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        for name, model in self.models.items():
            scores = cross_val_score(model, X, y, cv=cv, scoring='f1')
            print(f"{name:20s}: F1 = {scores.mean():.4f} (+/- {scores.std():.4f})")

    # ────────────────────────────────────────────────────────
    def plot_results(self, results, y_test,
                     save_path=None):
        if save_path is None:
            save_path = os.path.join(BASE_DIR, "model_comparison.png")

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. Metrics comparison
        metrics_df = pd.DataFrame(
            {name: [r['accuracy'], r['precision'], r['recall'], r['f1'], r['auc']]
             for name, r in results.items()},
            index=['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']
        )
        metrics_df.T.plot(kind='bar', ax=axes[0, 0])
        axes[0, 0].set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].legend(loc='lower right')
        axes[0, 0].grid(axis='y', alpha=0.3)
        plt.setp(axes[0, 0].xaxis.get_majorticklabels(), rotation=45, ha='right')

        # 2. ROC Curves
        for name, r in results.items():
            fpr, tpr, _ = roc_curve(y_test, r['y_proba'])
            axes[0, 1].plot(fpr, tpr, label=f"{name} (AUC={r['auc']:.3f})")
        axes[0, 1].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0, 1].set_xlabel('False Positive Rate')
        axes[0, 1].set_ylabel('True Positive Rate')
        axes[0, 1].set_title('ROC Curves', fontsize=14, fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)

        # 3. Confusion Matrix (best model)
        best_name = max(results.items(), key=lambda x: x[1]['f1'])[0]
        cm = confusion_matrix(y_test, results[best_name]['y_pred'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[1, 0])
        axes[1, 0].set_title(f'Confusion Matrix — {best_name}', fontsize=14, fontweight='bold')
        axes[1, 0].set_ylabel('True Label')
        axes[1, 0].set_xlabel('Predicted Label')

        # 4. Feature importance
        ax4 = axes[1, 1]
        if hasattr(results[best_name]['model'], 'feature_importances_'):
            importances = results[best_name]['model'].feature_importances_
            indices = np.argsort(importances)[-15:]
            ax4.barh(range(len(indices)), importances[indices])

            # Gán nhãn cho numeric features nếu biết vị trí
            n_tfidf = self.tfidf.get_feature_names_out().shape[0]
            labels = []
            for idx in indices:
                if idx < n_tfidf:
                    labels.append(f"tfidf[{idx}]")
                else:
                    feat_idx = idx - n_tfidf
                    if feat_idx < len(self.used_features):
                        labels.append(self.used_features[feat_idx])
                    else:
                        labels.append(str(idx))
            ax4.set_yticks(range(len(indices)))
            ax4.set_yticklabels(labels, fontsize=9)
            ax4.set_title(f'Top 15 Feature Importances — {best_name}',
                          fontsize=14, fontweight='bold')
            ax4.set_xlabel('Importance')
        else:
            ax4.text(0.5, 0.5, f'{best_name}\nno feature_importances_',
                     ha='center', va='center', fontsize=12)
            ax4.set_title('Feature Importances', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nĐã lưu biểu đồ: {save_path}")
        return fig

    # ────────────────────────────────────────────────────────
    def show_prediction_examples(self, df, idx_test, y_proba, y_test, n=5):
        print(f"\n{'='*80}\nVÍ DỤ DỰ ĐOÁN\n{'='*80}")
        for i, idx in enumerate(idx_test[:n]):
            row  = df.loc[idx]
            prob = y_proba[i]
            print(f"\n--- Mẫu #{i+1} ---")
            print(f"Tiêu đề : {str(row.get('Job Title','N/A'))[:80]}")
            print(f"Lương   : {row.get('Salary','N/A')}")
            print(f"Công ty : {row.get('Name Company', row.get('Company Size','N/A'))}")
            print(f"Thực tế : {'REAL' if y_test.iloc[i] == 1 else 'FAKE'}")
            print(f"Dự đoán : {'REAL' if prob > 0.5 else 'FAKE'} ({prob*100:.1f}%)")
            # In thêm company features nếu có
            if 'company_found' in row:
                print(f"MST found: {row['company_found']} | "
                      f"active: {row.get('company_active',0)} | "
                      f"rep: {row.get('reputation_score',0):.2f}")

    # ────────────────────────────────────────────────────────
    def run_complete_pipeline(self):
        # 1. Load
        df = self.load_and_prepare_data()
        print(f"\nPhân bố labels:\n{df['Label'].value_counts()}")
        print(f"Tỷ lệ FAKE: {(1 - df['Label'].mean())*100:.2f}%")

        # 2. Features
        X = self.prepare_features(df, fit=True)
        y = df['Label']
        print(f"\nShape: X={X.shape}, y={y.shape}")

        # 3. Split
        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, df.index, test_size=0.2, random_state=42, stratify=y
        )
        print(f"Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

        # 4. Train
        results = self.train_and_evaluate_models(X_train, X_test, y_train, y_test)

        # 5. Cross-validation
        self.cross_validation_evaluation(X, y)

        # 6. Ensemble
        voting_clf = self.create_voting_ensemble(results)
        voting_clf.fit(X_train, y_train)
        y_pred_ens  = voting_clf.predict(X_test)
        y_proba_ens = voting_clf.predict_proba(X_test)[:, 1]
        print(f"\n{'='*80}\nVOTING ENSEMBLE RESULTS\n{'='*80}")
        print(f"Accuracy : {accuracy_score(y_test, y_pred_ens):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred_ens, zero_division=0):.4f}")
        print(f"Recall   : {recall_score(y_test, y_pred_ens, zero_division=0):.4f}")
        print(f"F1-Score : {f1_score(y_test, y_pred_ens, zero_division=0):.4f}")
        print(f"AUC-ROC  : {roc_auc_score(y_test, y_proba_ens):.4f}")

        # 7. Best model
        best_name = max(results.items(), key=lambda x: x[1]['f1'])[0]
        self.best_model      = results[best_name]['model']
        self.best_model_name = best_name
        print(f"\nBest Single Model: {best_name} | F1={results[best_name]['f1']:.4f}")

        # 8. Plot
        self.plot_results(results, y_test)

        # 9. Report
        print(f"\n{'='*80}\nDETAILED REPORT — {best_name}\n{'='*80}")
        print(classification_report(y_test, results[best_name]['y_pred'],
                                    target_names=['FAKE', 'REAL']))

        # 10. Examples
        self.show_prediction_examples(df, idx_test, results[best_name]['y_proba'], y_test)

        return results, voting_clf


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import joblib

    print("=" * 80)
    print("HỆ THỐNG PHÂN LOẠI TIN TUYỂN DỤNG — ENSEMBLE MODELS")
    print("=" * 80)

    classifier = EnsembleJobClassifier(
        use_high_confidence_only=True,
        confidence_threshold=0.7
    )

    results, voting_clf = classifier.run_complete_pipeline()

    # Lưu models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(classifier.best_model,  os.path.join(MODEL_DIR, 'best_model.pkl'))
    joblib.dump(voting_clf,             os.path.join(MODEL_DIR, 'voting_ensemble.pkl'))
    joblib.dump(classifier.tfidf,       os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
    joblib.dump(classifier.scaler,      os.path.join(MODEL_DIR, 'scaler.pkl'))
    # Lưu thêm danh sách features đã dùng để predict runtime dùng đúng thứ tự
    joblib.dump(classifier.used_features, os.path.join(MODEL_DIR, 'feature_names.pkl'))

    print("\n" + "=" * 80)
    print("HOÀN THÀNH! Đã lưu: KHOA")
    for f in ['best_model.pkl', 'voting_ensemble.pkl',
              'tfidf_vectorizer.pkl', 'scaler.pkl', 'feature_names.pkl']:
        print(f"  models/{f}")