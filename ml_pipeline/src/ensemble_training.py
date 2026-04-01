import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from scipy.sparse import hstack
import matplotlib.pyplot as plt
import seaborn as sns

# Import các models
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import warnings
warnings.filterwarnings('ignore')


class EnsembleJobClassifier:
    """
    Hệ thống phân loại tin tuyển dụng với ensemble models
    """
    
    def __init__(self, use_high_confidence_only=True, confidence_threshold=0.7):
        self.use_high_confidence = use_high_confidence_only
        self.confidence_threshold = confidence_threshold
        
        # TF-IDF vectorizer
        self.tfidf = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),  # Tăng lên trigram
            min_df=3,
            max_df=0.8  # Loại bỏ từ xuất hiện quá nhiều
        )
        
        # Scaler cho numeric features
        self.scaler = StandardScaler()
        
        # Định nghĩa các models
        self.models = {
            'LogisticRegression': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                C=0.5,
                random_state=42
            ),
            'RandomForest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=4,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=150,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            ),
            'XGBoost': XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=1.5,  # Handle imbalance
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            ),
            'LightGBM': LGBMClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.1,
                class_weight='balanced',
                random_state=42,
                verbose=-1
            )
        }
        
        # Ensemble model
        self.voting_clf = None
        
        # Best single model
        self.best_model = None
        self.best_model_name = None
        
    def load_and_prepare_data(self):
        """Load và chuẩn bị dữ liệu"""
        print("Đang load dữ liệu...")
        
        # Load data với labels đã cải thiện
        df = pd.read_csv("../data/JOB_DATA_IMPROVED_LABELS.csv")
        # Lọc theo confidence nếu cần
        if self.use_high_confidence:
            original_size = len(df)
            df = df[df['confidence'] >= self.confidence_threshold]
            print(f"Lọc high-confidence: {original_size} -> {len(df)} mẫu")
        
        return df
    
    def prepare_features(self, df, fit=True):
        """Chuẩn bị features"""
        
        # 1. Text features (TF-IDF)
        X_text_raw = df['FULL_TEXT'].fillna("")
        
        if fit:
            X_text = self.tfidf.fit_transform(X_text_raw)
        else:
            X_text = self.tfidf.transform(X_text_raw)
        
        # 2. Numeric features (engineered features)
        numeric_features = [
            # Text features
            'text_length', 'char_length', 'avg_word_length',
            'uppercase_ratio', 'exclamation_count', 'number_count',
            'vocab_diversity', 'scam_keyword_count', 'positive_keyword_count',
            'max_word_repetition',
            
            # Salary features
            'salary_missing', 'salary_negotiable', 'salary_avg',
            'salary_range_width', 'salary_suspiciously_high', 'salary_too_low',
            
            # Company features
            'company_size_missing', 'company_size_value', 'is_small_company',
            'company_overview_length', 'company_overview_missing',
            
            # Requirement features
            'no_experience_required', 'experience_years',
            'num_candidates', 'mass_recruitment',
            'requirements_length', 'requirements_missing',
            
            # Career level & Job type features
            'is_management_level', 'is_entry_level',
            'is_part_time', 'is_full_time', 'is_freelance'
        ]
        
        # Lọc các features có trong data
        available_features = [f for f in numeric_features if f in df.columns]
        print(f"Sử dụng {len(available_features)} numeric features")
        
        X_num = df[available_features].fillna(0)
        
        if fit:
            X_num_scaled = self.scaler.fit_transform(X_num)
        else:
            X_num_scaled = self.scaler.transform(X_num)
        
        # 3. Combine
        X = hstack([X_text, X_num_scaled])
        
        return X
    
    def train_and_evaluate_models(self, X_train, X_test, y_train, y_test):
        """Train và đánh giá từng model"""
        
        results = {}
        
        print("\n" + "="*80)
        print("TRAINING VÀ ĐÁNH GIÁ CÁC MODELS")
        print("="*80)
        
        for name, model in self.models.items():
            print(f"\n[{name}]")
            print("-" * 40)
            
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            
            # Metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'auc': auc,
                'y_pred': y_pred,
                'y_proba': y_proba
            }
            
            print(f"Accuracy:  {accuracy:.4f}")
            print(f"Precision: {precision:.4f}")
            print(f"Recall:    {recall:.4f}")
            print(f"F1-Score:  {f1:.4f}")
            print(f"AUC-ROC:   {auc:.4f}")
        
        return results
    
    def create_voting_ensemble(self, results):
        """Tạo voting ensemble từ các models tốt nhất"""
        
        # Chọn top 3 models theo F1-score
        sorted_models = sorted(results.items(), key=lambda x: x[1]['f1'], reverse=True)
        top_3 = sorted_models[:3]
        
        print(f"\n\nTop 3 models cho Voting Ensemble:")
        for name, result in top_3:
            print(f"  {name}: F1={result['f1']:.4f}, AUC={result['auc']:.4f}")
        
        # Tạo voting classifier
        estimators = [(name, result['model']) for name, result in top_3]
        
        self.voting_clf = VotingClassifier(
            estimators=estimators,
            voting='soft',  # Sử dụng probability
            weights=[3, 2, 1]  # Trọng số cho top 3
        )
        
        return self.voting_clf
    
    def cross_validation_evaluation(self, X, y):
        """Đánh giá cross-validation"""
        
        print("\n" + "="*80)
        print("CROSS-VALIDATION (5-FOLD)")
        print("="*80)
        
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        for name, model in self.models.items():
            scores = cross_val_score(model, X, y, cv=cv, scoring='f1')
            print(f"{name:20s}: F1 = {scores.mean():.4f} (+/- {scores.std():.4f})")
    
    def plot_results(self, results, y_test, save_path="model_comparison.png"):
        """Vẽ biểu đồ so sánh models"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Metrics comparison
        ax1 = axes[0, 0]
        metrics_df = pd.DataFrame({
            name: [r['accuracy'], r['precision'], r['recall'], r['f1'], r['auc']]
            for name, r in results.items()
        }, index=['Accuracy', 'Precision', 'Recall', 'F1', 'AUC'])
        
        metrics_df.T.plot(kind='bar', ax=ax1)
        ax1.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Score')
        ax1.set_xlabel('Model')
        ax1.legend(loc='lower right')
        ax1.grid(axis='y', alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 2. ROC Curves
        ax2 = axes[0, 1]
        for name, result in results.items():
            fpr, tpr, _ = roc_curve(y_test, result['y_proba'])
            ax2.plot(fpr, tpr, label=f"{name} (AUC={result['auc']:.3f})")
        
        ax2.plot([0, 1], [0, 1], 'k--', label='Random')
        ax2.set_xlabel('False Positive Rate')
        ax2.set_ylabel('True Positive Rate')
        ax2.set_title('ROC Curves', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        # 3. Confusion Matrix (best model)
        best_name = max(results.items(), key=lambda x: x[1]['f1'])[0]
        best_result = results[best_name]
        
        ax3 = axes[1, 0]
        cm = confusion_matrix(y_test, best_result['y_pred'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax3)
        ax3.set_title(f'Confusion Matrix - {best_name}', fontsize=14, fontweight='bold')
        ax3.set_ylabel('True Label')
        ax3.set_xlabel('Predicted Label')
        
        # 4. Feature importance (nếu có)
        ax4 = axes[1, 1]
        if hasattr(best_result['model'], 'feature_importances_'):
            importances = best_result['model'].feature_importances_
            
            # Lấy top 15 features
            indices = np.argsort(importances)[-15:]
            
            # Lưu ý: Khó map exact feature names do có TF-IDF
            # Chỉ hiển thị numeric features
            ax4.barh(range(len(indices)), importances[indices])
            ax4.set_title(f'Top 15 Feature Importances - {best_name}', 
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
    
    def run_complete_pipeline(self):
        """Chạy toàn bộ pipeline"""
        
        # 1. Load data
        df = self.load_and_prepare_data()
        
        print(f"\nPhân bố labels:")
        print(df['Label'].value_counts())
        print(f"Tỷ lệ FAKE: {(1 - df['Label'].mean())*100:.2f}%")
        
        # 2. Prepare features
        X = self.prepare_features(df, fit=True)
        y = df['Label']
        
        print(f"\nShape: X={X.shape}, y={y.shape}")
        
        # 3. Train/Test split
        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, df.index,
            test_size=0.2,
            random_state=42,
            stratify=y
        )
        
        print(f"Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")
        
        # 4. Train và evaluate từng model
        results = self.train_and_evaluate_models(X_train, X_test, y_train, y_test)
        
        # 5. Cross-validation
        self.cross_validation_evaluation(X, y)
        
        # 6. Tạo ensemble
        voting_clf = self.create_voting_ensemble(results)
        voting_clf.fit(X_train, y_train)
        
        # Evaluate ensemble
        y_pred_ensemble = voting_clf.predict(X_test)
        y_proba_ensemble = voting_clf.predict_proba(X_test)[:, 1]
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        print(f"\n\n{'='*80}")
        print("VOTING ENSEMBLE RESULTS")
        print("="*80)
        print(f"Accuracy:  {accuracy_score(y_test, y_pred_ensemble):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred_ensemble):.4f}")
        print(f"Recall:    {recall_score(y_test, y_pred_ensemble):.4f}")
        print(f"F1-Score:  {f1_score(y_test, y_pred_ensemble):.4f}")
        print(f"AUC-ROC:   {roc_auc_score(y_test, y_proba_ensemble):.4f}")
        
        # 7. Tìm best single model
        best_name = max(results.items(), key=lambda x: x[1]['f1'])[0]
        self.best_model = results[best_name]['model']
        self.best_model_name = best_name
        
        print(f"\n\nBest Single Model: {best_name}")
        print(f"F1-Score: {results[best_name]['f1']:.4f}")
        
        # 8. Plot results
        self.plot_results(results, y_test)
        
        # 9. Detailed report cho best model
        print(f"\n\n{'='*80}")
        print(f"DETAILED REPORT - {best_name}")
        print("="*80)
        print(classification_report(y_test, results[best_name]['y_pred'], 
                                   target_names=['FAKE', 'REAL']))
        
        # 10. Ví dụ dự đoán
        self.show_prediction_examples(df, idx_test, results[best_name]['y_proba'], y_test)
        
        return results, voting_clf
    
    def show_prediction_examples(self, df, idx_test, y_proba, y_test, n_examples=5):
        """Hiển thị ví dụ dự đoán"""
        
        print(f"\n\n{'='*80}")
        print("VÍ DỤ DỰ ĐOÁN")
        print("="*80)
        
        test_indices = idx_test[:n_examples]
        
        for i, idx in enumerate(test_indices):
            row = df.loc[idx]
            prob = y_proba[i]
            actual = y_test.iloc[i]
            predicted = 1 if prob > 0.5 else 0
            
            print(f"\n--- Mẫu #{i+1} ---")
            print(f"Tiêu đề: {row.get('Job Title', 'N/A')[:80]}")
            print(f"Lương: {row.get('Salary', 'N/A')}")
            print(f"Công ty: {row.get('Company Size', 'N/A')}")
            print(f"Thực tế: {'REAL' if actual == 1 else 'FAKE'}")
            print(f"Dự đoán: {'REAL' if predicted == 1 else 'FAKE'}")
            print(f"Xác suất REAL: {prob*100:.2f}%")
            print(f"Confidence: {row.get('confidence', 'N/A')}")
            
            if 'rule_reasons' in row and row['Label'] == 0:
                print(f"Lý do: {row['rule_reasons']}")


# MAIN
if __name__ == "__main__":
    
    print("="*80)
    print("HỆ THỐNG PHÂN LOẠI TIN TUYỂN DỤNG - ENSEMBLE MODELS")
    print("="*80)
    
    # Khởi tạo classifier
    classifier = EnsembleJobClassifier(
        use_high_confidence_only=True,
        confidence_threshold=0.7
    )
    
    # Chạy toàn bộ pipeline
    results, voting_clf = classifier.run_complete_pipeline()
    
    print("\n\n" + "="*80)
    print("HOÀN THÀNH!")
    print("="*80)
    print("\nĐã tạo các file:")
    print("  - model_comparison.png: Biểu đồ so sánh models")
    
    # Save models
    import joblib
    
    joblib.dump(classifier.best_model, 'best_model.pkl')
    joblib.dump(voting_clf, 'voting_ensemble.pkl')
    joblib.dump(classifier.tfidf, 'tfidf_vectorizer.pkl')
    joblib.dump(classifier.scaler, 'scaler.pkl')
    
    print("  - best_model.pkl: Best single model")
    print("  - voting_ensemble.pkl: Ensemble model")
    print("  - tfidf_vectorizer.pkl: TF-IDF vectorizer")
    print("  - scaler.pkl: Feature scaler")
