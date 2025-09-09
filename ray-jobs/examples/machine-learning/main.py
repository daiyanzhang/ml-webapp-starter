#!/usr/bin/env python3
"""
独立的Ray Job脚本 - 机器学习任务
在Ray集群上作为独立Job运行
"""
import ray
import sys
import json
import time
import os
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 导入调试工具（可选）
from debug_utils import log_info, log_error


@ray.remote
def create_dataset(
    n_samples: int, n_features: int, n_classes: int, random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """创建分类数据集"""
    log_info(
        f"Creating dataset with {n_samples} samples, {n_features} features, {n_classes} classes"
    )

    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_classes=n_classes,
        n_informative=min(n_features, n_classes * 2),
        n_redundant=max(0, n_features - n_classes * 2),
        random_state=random_state,
    )

    return X, y


@ray.remote
def train_model(
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_id: int,
) -> Dict[str, Any]:
    """训练单个模型"""
    log_info(f"Training {model_type} model (ID: {model_id})")

    start_time = time.time()

    # 选择模型
    if model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=1)
    elif model_type == "logistic_regression":
        model = LogisticRegression(random_state=42, max_iter=1000)
    elif model_type == "svm":
        model = SVC(random_state=42, probability=True)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # 训练模型
    model.fit(X_train, y_train)

    # 预测和评估
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # 获取分类报告
    report = classification_report(y_test, y_pred, output_dict=True)

    training_time = time.time() - start_time

    result = {
        "model_id": model_id,
        "model_type": model_type,
        "accuracy": float(accuracy),
        "training_time_seconds": float(training_time),
        "classification_report": report,
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "n_features": X_train.shape[1],
    }

    log_info(
        f"Model {model_type} (ID: {model_id}) completed with accuracy: {accuracy:.4f}"
    )
    return result


def main():
    """主函数 - 作为独立Ray Job运行"""
    # 从环境变量获取参数
    job_id = os.environ.get("RAY_JOB_ID", "unknown")
    task_type = os.environ.get("TASK_TYPE", "machine_learning")
    params_str = os.environ.get("TASK_PARAMS", "{}")

    try:
        params = json.loads(params_str)
    except:
        params = {}

    log_info("=== Ray Machine Learning Job Started ===")
    log_info(f"Job ID: {job_id}")
    log_info(f"Task Type: {task_type}")
    log_info(f"Parameters: {params}")

    # 连接到Ray集群
    if not ray.is_initialized():
        ray.init()

    start_time = datetime.now()

    # 获取参数
    n_samples = params.get("n_samples", 10000)
    n_features = params.get("n_features", 20)
    n_classes = params.get("n_classes", 3)
    n_models = params.get("n_models", 3)

    log_info(
        f"Training {n_models} models on dataset with {n_samples} samples, {n_features} features, {n_classes} classes"
    )

    # 第一步：创建数据集
    log_info("Step 1: Creating dataset...")
    dataset_future = create_dataset.remote(n_samples, n_features, n_classes)
    X, y = ray.get(dataset_future)

    # 划分训练和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    log_info(f"Dataset created: {len(X_train)} train samples, {len(X_test)} test samples")

    # 第二步：并行训练多个模型
    log_info("Step 2: Training models in parallel...")

    model_types = ["random_forest", "logistic_regression", "svm"]
    model_futures = []

    for i in range(n_models):
        model_type = model_types[i % len(model_types)]
        future = train_model.remote(model_type, X_train, y_train, X_test, y_test, i)
        model_futures.append(future)

    log_info(f"Started training {len(model_futures)} models")

    # 收集训练结果
    model_results = ray.get(model_futures)

    # 第三步：分析结果
    log_info("Step 3: Analyzing results...")

    # 找到最佳模型
    best_model = max(model_results, key=lambda x: x["accuracy"])
    avg_accuracy = np.mean([result["accuracy"] for result in model_results])
    total_training_time = sum(
        [result["training_time_seconds"] for result in model_results]
    )

    # 按模型类型分组统计
    type_stats = {}
    for result in model_results:
        model_type = result["model_type"]
        if model_type not in type_stats:
            type_stats[model_type] = []
        type_stats[model_type].append(result["accuracy"])

    type_summary = {}
    for model_type, accuracies in type_stats.items():
        type_summary[model_type] = {
            "count": len(accuracies),
            "avg_accuracy": float(np.mean(accuracies)),
            "max_accuracy": float(np.max(accuracies)),
            "min_accuracy": float(np.min(accuracies)),
        }

    # 构建最终结果
    final_result = {
        "job_id": job_id,
        "task_type": task_type,
        "parameters": params,
        "result": {
            "ml_summary": {
                "dataset_info": {
                    "total_samples": n_samples,
                    "train_samples": len(X_train),
                    "test_samples": len(X_test),
                    "features": n_features,
                    "classes": n_classes,
                },
                "models_trained": len(model_results),
                "total_training_time_seconds": float(total_training_time),
                "average_accuracy": float(avg_accuracy),
                "best_model": best_model,
                "model_type_summary": type_summary,
            },
            "individual_results": model_results,
        },
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat(),
        "status": "completed",
    }

    log_info(f"=== Ray Machine Learning Job Logic Completed ===")
    log_info(
        f"Trained {len(model_results)} models with average accuracy: {avg_accuracy:.4f}"
    )
    log_info(
        f"Best model: {best_model['model_type']} with accuracy: {best_model['accuracy']:.4f}"
    )

    return final_result


if __name__ == "__main__":
    main()
