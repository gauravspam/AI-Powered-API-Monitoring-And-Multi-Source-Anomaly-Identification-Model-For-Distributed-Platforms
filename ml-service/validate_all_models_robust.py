import os
import json
import numpy as np
import tensorflow as tf
from pathlib import Path
import pickle
from datetime import datetime

# Define FocalLoss
@tf.keras.utils.register_keras_serializable(package="CustomLosses")
class FocalLoss(tf.keras.losses.Loss):
    def __init__(self, alpha=0.25, gamma=2.0, name='focal_loss', **kwargs):
        super().__init__(name=name, **kwargs)
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon())
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = self.alpha * y_true * tf.pow((1 - y_pred), self.gamma)
        focal_loss = weight * cross_entropy
        return tf.reduce_mean(tf.reduce_sum(focal_loss, axis=1))

    def get_config(self):
        config = super().get_config()
        config.update({
            "alpha": self.alpha,
            "gamma": self.gamma
        })
        return config

class ModelValidator:
    def __init__(self, base_path="models"):
        self.base_path = Path(base_path)
        self.results = {}

    def load_model_and_metadata(self, dataset_name, model_type):
        """Load model, scaler, and metadata for a specific dataset and model type"""
        dataset_path = self.base_path / dataset_name

        try:
            # Load model with custom objects
            model_file = dataset_path / f"{model_type}_model.keras"
            custom_objects = {'FocalLoss': FocalLoss}
            model = tf.keras.models.load_model(model_file, custom_objects=custom_objects)

            # Load scaler
            scaler_file = dataset_path / "scaler.pkl"
            if model_type == "ple_gru" and (dataset_path / "ple_gru_scaler.pkl").exists():
                scaler_file = dataset_path / "ple_gru_scaler.pkl"
            elif model_type == "msif_lstm" and (dataset_path / "msif_lstm_scaler.pkl").exists():
                scaler_file = dataset_path / "msif_lstm_scaler.pkl"

            with open(scaler_file, 'rb') as f:
                scaler = pickle.load(f)

            # Load metadata
            metadata_file = dataset_path / "metadata.json"
            if model_type == "ple_gru" and (dataset_path / "ple_gru_metadata.json").exists():
                metadata_file = dataset_path / "ple_gru_metadata.json"

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            return model, scaler, metadata
        except Exception as e:
            return None, None, {"error": str(e)}

    def validate_model_architecture(self, model, model_type):
        """Validate model architecture and parameters"""
        if model is None:
            return {"status": "FAILED", "reason": "Model not loaded"}

        try:
            total_params = model.count_params()
            trainable_params = sum([tf.keras.backend.count_params(w) for w in model.trainable_weights])

            # Check input/output shapes
            input_shape = model.input_shape
            output_shape = model.output_shape

            # Verify model type matches architecture
            layer_types = [layer.__class__.__name__ for layer in model.layers]

            if model_type == "msif_lstm" and "LSTM" not in str(layer_types):
                return {"status": "WARNING", "reason": "MSIF-LSTM model missing LSTM layers"}
            elif model_type == "ple_gru" and "GRU" not in str(layer_types):
                return {"status": "WARNING", "reason": "PLE-GRU model missing GRU layers"}

            return {
                "status": "PASSED",
                "total_params": int(total_params),
                "trainable_params": int(trainable_params),
                "input_shape": str(input_shape),
                "output_shape": str(output_shape),
                "layers": len(model.layers),
                "layer_types": layer_types
            }
        except Exception as e:
            return {"status": "FAILED", "reason": str(e)}

    def validate_inference(self, model, scaler, model_type):
        """Test inference with synthetic data"""
        if model is None or scaler is None:
            return {"status": "FAILED", "reason": "Model or scaler not loaded"}

        try:
            # ROBUST INPUT SHAPE HANDLING
            input_shape = model.input_shape
            batch_size = 32

            # Determine correct input dimensions based on shape tuple length
            if len(input_shape) == 3:  # (None, timesteps, features)
                timesteps = input_shape[1]
                features = input_shape[2]
                test_data = np.random.randn(batch_size, timesteps, features).astype(np.float32)
            elif len(input_shape) == 2:  # (None, features)
                features = input_shape[1]
                test_data = np.random.randn(batch_size, features).astype(np.float32)
            else:
                # Fallback for dynamic shapes or unexpected tuples
                return {"status": "FAILED", "reason": f"Unexpected input shape: {input_shape}"}

            # Run inference
            predictions = model.predict(test_data, verbose=0)

            # Validate predictions
            pred_shape = predictions.shape
            pred_min = float(np.min(predictions))
            pred_max = float(np.max(predictions))
            pred_mean = float(np.mean(predictions))
            pred_std = float(np.std(predictions))

            # Check if predictions are in valid range (0-1 for anomaly detection)
            if pred_min < -0.1 or pred_max > 1.1:
                status = "WARNING"
                reason = f"Predictions outside expected [0,1] range: [{pred_min:.4f}, {pred_max:.4f}]"
            elif pred_std < 0.001:
                status = "WARNING"
                reason = f"Very low variance ({pred_std:.6f}) - all predictions nearly identical at {pred_mean:.4f}"
            else:
                status = "PASSED"
                reason = "Inference successful with varied predictions"

            return {
                "status": status,
                "reason": reason,
                "prediction_shape": str(pred_shape),
                "pred_min": pred_min,
                "pred_max": pred_max,
                "pred_mean": pred_mean,
                "pred_std": pred_std,
                "inference_batch_size": batch_size
            }
        except Exception as e:
            return {"status": "FAILED", "reason": str(e)}

    def validate_metadata(self, metadata, model_type):
        """Validate metadata completeness"""
        if "error" in metadata:
            return {"status": "FAILED", "reason": metadata["error"]}

        required_fields = ["f1_score", "precision", "recall"]

        # Check if metadata has model-specific metrics
        model_metadata = metadata.get(model_type, metadata)

        # Check for alternative field names
        available_fields = list(model_metadata.keys())
        missing_fields = []

        for field in required_fields:
            if field not in model_metadata:
                # Check nested metrics dictionary
                if 'metrics' in model_metadata and field in model_metadata['metrics']:
                    continue
                missing_fields.append(field)

        if missing_fields and len(available_fields) == 0:
            return {
                "status": "FAILED",
                "reason": "No metadata fields found"
            }

        if missing_fields:
            return {
                "status": "WARNING",
                "reason": f"Missing fields: {missing_fields}",
                "available_fields": available_fields,
                "metadata_content": model_metadata
            }

        # Extract performance metrics
        if 'metrics' in model_metadata:
             metrics = model_metadata['metrics']
             f1 = metrics.get("f1_score", 0)
             precision = metrics.get("precision", 0)
             recall = metrics.get("recall", 0)
             accuracy = metrics.get("accuracy", 0)
             auc = metrics.get("auc", 0)
        else:
             f1 = model_metadata.get("f1_score", 0)
             precision = model_metadata.get("precision", 0)
             recall = model_metadata.get("recall", 0)
             accuracy = model_metadata.get("accuracy", 0)
             auc = model_metadata.get("auc", 0)

        # Performance assessment
        if f1 >= 0.95:
            performance = "EXCELLENT ⭐"
        elif f1 >= 0.90:
            performance = "GOOD ✅"
        elif f1 >= 0.80:
            performance = "MODERATE ⚠️"
        else:
            performance = "NEEDS_IMPROVEMENT ❌"

        return {
            "status": "PASSED",
            "performance": performance,
            "f1_score": f1,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
            "auc": auc
        }

    def validate_dataset_model(self, dataset_name, model_type):
        """Validate a specific model for a dataset"""
        print(f"\n{'='*70}")
        print(f"Validating: {dataset_name.upper()} - {model_type.upper()}")
        print('='*70)

        # Load model components
        model, scaler, metadata = self.load_model_and_metadata(dataset_name, model_type)

        # Run validation tests
        arch_result = self.validate_model_architecture(model, model_type)
        infer_result = self.validate_inference(model, scaler, model_type)
        meta_result = self.validate_metadata(metadata, model_type)

        # Compile results
        result = {
            "dataset": dataset_name,
            "model_type": model_type,
            "architecture": arch_result,
            "inference": infer_result,
            "metadata": meta_result,
            "timestamp": datetime.now().isoformat()
        }

        # Determine overall status
        statuses = [arch_result["status"], infer_result["status"], meta_result["status"]]
        if "FAILED" in statuses:
            overall = "❌ FAILED"
        elif "WARNING" in statuses:
            overall = "⚠️  WARNING"
        else:
            overall = "✅ PASSED"

        result["overall_status"] = overall

        # Print summary
        print(f"\nArchitecture: {arch_result['status']}")
        if arch_result['status'] == 'PASSED':
            print(f"  - Parameters: {arch_result['total_params']:,}")
            print(f"  - Layers: {arch_result['layers']}")
            print(f"  - Input: {arch_result['input_shape']}")
            print(f"  - Output: {arch_result['output_shape']}")
        else:
            print(f"  - Reason: {arch_result.get('reason', 'Unknown')}")

        print(f"\nInference: {infer_result['status']}")
        if infer_result['status'] in ['PASSED', 'WARNING']:
            print(f"  - Prediction Range: [{infer_result['pred_min']:.4f}, {infer_result['pred_max']:.4f}]")
            print(f"  - Mean: {infer_result['pred_mean']:.4f}")
            print(f"  - Std Dev: {infer_result['pred_std']:.4f}")
            if infer_result['status'] == 'WARNING':
                print(f"  - Warning: {infer_result['reason']}")
        else:
            print(f"  - Reason: {infer_result.get('reason', 'Unknown')}")

        print(f"\nMetadata: {meta_result['status']}")
        if meta_result['status'] == 'PASSED':
            print(f"  - Performance: {meta_result['performance']}")
            print(f"  - F1 Score: {meta_result['f1_score']:.4f}")
            print(f"  - Precision: {meta_result['precision']:.4f}")
            print(f"  - Recall: {meta_result['recall']:.4f}")
        elif meta_result['status'] == 'WARNING':
            print(f"  - Warning: {meta_result.get('reason', 'Unknown')}")
            print(f"  - Available fields: {meta_result.get('available_fields', [])}")
        else:
            print(f"  - Reason: {meta_result.get('reason', 'Unknown')}")

        print(f"\n{'='*70}")
        print(f"Overall Status: {overall}")
        print('='*70)

        return result

    def validate_all(self):
        """Validate all models across all datasets"""
        datasets = ["nab", "microservices", "lo2"]
        model_types = ["msif_lstm", "ple_gru"]

        print("\n" + "="*70)
        print("MODEL VALIDATION REPORT")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        all_results = []
        summary = {"passed": 0, "warning": 0, "failed": 0}

        for dataset in datasets:
            for model_type in model_types:
                result = self.validate_dataset_model(dataset, model_type)
                all_results.append(result)

                if "✅" in result["overall_status"]:
                    summary["passed"] += 1
                elif "⚠️" in result["overall_status"]:
                    summary["warning"] += 1
                else:
                    summary["failed"] += 1

        # Print final summary
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Models: {len(all_results)}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"⚠️  Warning: {summary['warning']}")
        print(f"❌ Failed: {summary['failed']}")

        # Overall health
        pass_rate = summary['passed'] / len(all_results) * 100
        warn_rate = summary['warning'] / len(all_results) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")
        print(f"Warning Rate: {warn_rate:.1f}%")

        if pass_rate == 100:
            health = "🎉 EXCELLENT - All models validated successfully!"
        elif pass_rate >= 66:
            health = "✅ GOOD - Most models working, some warnings"
        elif pass_rate >= 33:
            health = "⚠️  MODERATE - Several models need attention"
        else:
            health = "❌ CRITICAL - Major validation issues"

        print(f"Overall Health: {health}")
        print("="*70)

        # Save detailed report
        report = {
            "summary": summary,
            "total_models": len(all_results),
            "pass_rate": pass_rate,
            "warning_rate": warn_rate,
            "health": health,
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }

        with open("validation_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n📄 Detailed report saved to: validation_report.json")

        return report

if __name__ == "__main__":
    validator = ModelValidator()
    report = validator.validate_all()
