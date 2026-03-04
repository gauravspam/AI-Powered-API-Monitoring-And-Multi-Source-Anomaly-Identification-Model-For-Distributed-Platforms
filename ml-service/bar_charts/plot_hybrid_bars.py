

import matplotlib.pyplot as plt
import numpy as np
from hybrid_data import (
    ACCURACY,
    EPOCHS,
    F1_SCORE,
    PRECISION,
    RECALL,
    TRAIN_PERCENTS,
)


def plot_metric(metric_matrix, metric_name, output_path):
    """
    metric_matrix: numpy array shape 7 by 5
    metric_name: string, for example "Accuracy"
    output_path: file path for saving the figure
    """

    train_labels = [f"{p}%" for p in TRAIN_PERCENTS]
    num_train = len(TRAIN_PERCENTS)
    num_epochs = len(EPOCHS)

    x_index = np.arange(num_train)
    bar_width = 0.18

    colors = [
        "#F1C40F",  # epoch 10
        "#E67E22",  # epoch 20
        "#E74C3C",  # epoch 30
        "#3498DB",  # epoch 40
        "#2ECC71",  # epoch 50
    ]

    plt.figure(figsize=(12, 6))

    for j in range(num_epochs):
        offset = (j - (num_epochs - 1) / 2) * bar_width
        positions = x_index + offset
        plt.bar(
            positions,
            metric_matrix[:, j],
            width=bar_width,
            color=colors[j],
            label=f"{EPOCHS[j]}",
            edgecolor="black",
            linewidth=0.7,
        )

    plt.xticks(x_index, train_labels, fontsize=11)
    plt.yticks(np.arange(0, 101, 20), fontsize=11)
    plt.ylim(0, 100)

    plt.xlabel("Training data (%)", fontsize=13)
    plt.ylabel(f"{metric_name} (%)", fontsize=13)
    plt.title(f"{metric_name} Comparision of Machine Learning Models on Train Ticket (AIOps Challenge 2020)", fontsize=15, fontweight="bold")
    plt.legend(
        title="Models",
        fontsize=10,
        title_fontsize=11,
        loc="upper left",
        bbox_to_anchor=(0.00, 0.10),
        ncols=2,
        nrows=3,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    plot_metric(ACCURACY, "Accuracy", "hybrid_accuracy.png")
    plot_metric(PRECISION, "Precision", "hybrid_precision.png")
    plot_metric(RECALL, "Recall", "hybrid_recall.png")
    plot_metric(F1_SCORE, "F1 Score", "hybrid_f1.png")


if __name__ == "__main__":
    main()
