# import os

# import matplotlib.pyplot as plt
# import numpy as np

# # figure size and style
# plt.style.use('seaborn-v0_8')
# plt.rcParams.update({
#     'font.size': 12,
#     'axes.titlesize': 14,
#     'axes.labelsize': 12,
#     'xtick.labelsize': 10,
#     'ytick.labelsize': 10,
#     'legend.fontsize': 10,
#     'figure.titlesize': 16,
#     'figure.figsize': (12, 8)
# })

# # training data percentages
# training_percentages = [40, 50, 60, 70, 80, 90, 100]
# x = np.arange(len(training_percentages))  # the label locations

# # bar width
# width = 0.25  # the width of the bars

# # colors
# colors = {
#     'MSIF-LSTM': '#FADB14',      # yellow
#     'PLE-GRU': '#F39C12',        # orange
#     'Hybrid Fusion': '#E74C3C'   # red
# }


# # Accuracy data (%)
# accuracy_data = {
#     'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
#     'PLE-GRU':  [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
#     'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
# }

# # Precision data (%)
# precision_data = {
#     'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
#     'PLE-GRU':[87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
#     'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
# }

# # Recall data (%)
# recall_data = {
#     'MSIF-LSTM': [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
#     'PLE-GRU': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
#     'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
# }

# # F1-Score data (%)
# f1_data = {
#     'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
#     'PLE-GRU': [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
#     'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4],
# }

# # subplots for the four metrics
# fig, axes = plt.subplots(2, 2, figsize=(14, 12))
# fig.suptitle('Performance Comparison of MSIF-LSTM, PLE-GRU, and Hybrid Fusion Models', fontsize=16, fontweight='bold')

# # Plot Accuracy
# ax = axes[0, 0]
# bars1 = ax.bar(x - width, accuracy_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
# bars2 = ax.bar(x, accuracy_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
# bars3 = ax.bar(x + width, accuracy_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

# ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
# ax.set_ylabel('Accuracy (%)', fontsize=12)
# ax.set_title('Accuracy Comparison', fontsize=14, fontweight='bold')
# ax.set_xticks(x)
# ax.set_xticklabels([f'{p}%' for p in training_percentages])
# ax.set_ylim(0, 100)
# ax.grid(axis='y', alpha=0.3)
# ax.legend(loc='upper left')

# # Plot Precision
# ax = axes[0, 1]
# bars1 = ax.bar(x - width, precision_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
# bars2 = ax.bar(x, precision_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
# bars3 = ax.bar(x + width, precision_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

# ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
# ax.set_ylabel('Precision (%)', fontsize=12)
# ax.set_title('Precision Comparison', fontsize=14, fontweight='bold')
# ax.set_xticks(x)
# ax.set_xticklabels([f'{p}%' for p in training_percentages])
# ax.set_ylim(0, 100)
# ax.grid(axis='y', alpha=0.3)
# ax.legend(loc='upper left')

# # Plot Recall
# ax = axes[1, 0]
# bars1 = ax.bar(x - width, recall_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
# bars2 = ax.bar(x, recall_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
# bars3 = ax.bar(x + width, recall_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

# ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
# ax.set_ylabel('Recall (%)', fontsize=12)
# ax.set_title('Recall Comparison', fontsize=14, fontweight='bold')
# ax.set_xticks(x)
# ax.set_xticklabels([f'{p}%' for p in training_percentages])
# ax.set_ylim(0, 100)
# ax.grid(axis='y', alpha=0.3)
# ax.legend(loc='upper left')

# # Plot F1-Score
# ax = axes[1, 1]
# bars1 = ax.bar(x - width, f1_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
# bars2 = ax.bar(x, f1_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
# bars3 = ax.bar(x + width, f1_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

# ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
# ax.set_ylabel('F1-Score (%)', fontsize=12)
# ax.set_title('F1-Score Comparison', fontsize=14, fontweight='bold')
# ax.set_xticks(x)
# ax.set_xticklabels([f'{p}%' for p in training_percentages])
# ax.set_ylim(0, 100)
# ax.grid(axis='y', alpha=0.3)
# ax.legend(loc='upper left')

# # Adjust layout to prevent overlap
# plt.tight_layout()

# # Save the figure
# output_dir = os.path.join(os.path.dirname(__file__), 'plots')
# os.makedirs(output_dir, exist_ok=True)
# output_path = os.path.join(output_dir, 'model_performance_comparison.png')
# plt.savefig(output_path, dpi=300, bbox_inches='tight')
# print(f"✅ Charts saved to: {output_path}")

# # Show the plot
# plt.show()






import os

import matplotlib.pyplot as plt
import numpy as np

# figure size and style
plt.style.use('seaborn-v0_8')
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'figure.figsize': (12, 8)
})

# training data percentages
training_percentages = [40, 50, 60, 70, 80, 90, 100]
x = np.arange(len(training_percentages))  # the label locations

# bar width
width = 0.25  # the width of the bars

# colors
colors = {
    'MSIF-LSTM': '#FADB14',      # yellow
    'PLE-GRU': '#F39C12',        # orange
    'Hybrid Fusion': '#E74C3C'   # red
}

# Accuracy data (%)
accuracy_data = {
    'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
    'PLE-GRU':  [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
    'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
}

# Precision data (%)
precision_data = {
    'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
    'PLE-GRU':[87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
    'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
}

# Recall data (%)
recall_data = {
    'MSIF-LSTM': [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
    'PLE-GRU': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
    'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4]
}

# F1-Score data (%)
f1_data = {
    'MSIF-LSTM': [88.8, 86.2, 89.8, 90.4, 89.2, 90.1, 93.83],
    'PLE-GRU': [87.0, 88.6, 89.1, 91.7, 91.6, 91.6, 93.33],
    'Hybrid Fusion': [90.3, 90.8, 93.4, 94.1, 93.0, 93.1, 96.4],
}

# subplots for the four metrics
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Performance Comparison of MSIF-LSTM, PLE-GRU, and Hybrid Fusion Models', fontsize=16, fontweight='bold')

# Plot Accuracy
ax = axes[0, 0]
bars1 = ax.bar(x - width, accuracy_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
bars2 = ax.bar(x, accuracy_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
bars3 = ax.bar(x + width, accuracy_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
ax.set_ylabel('Accuracy (%)', fontsize=12)
ax.set_title('Accuracy Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{p}%' for p in training_percentages])
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3)

# Plot Precision
ax = axes[0, 1]
bars1 = ax.bar(x - width, precision_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
bars2 = ax.bar(x, precision_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
bars3 = ax.bar(x + width, precision_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
ax.set_ylabel('Precision (%)', fontsize=12)
ax.set_title('Precision Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{p}%' for p in training_percentages])
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3)

# Plot Recall
ax = axes[1, 0]
bars1 = ax.bar(x - width, recall_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
bars2 = ax.bar(x, recall_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
bars3 = ax.bar(x + width, recall_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
ax.set_ylabel('Recall (%)', fontsize=12)
ax.set_title('Recall Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{p}%' for p in training_percentages])
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3)

# Plot F1-Score
ax = axes[1, 1]
bars1 = ax.bar(x - width, f1_data['MSIF-LSTM'], width, label='MSIF-LSTM', color=colors['MSIF-LSTM'])
bars2 = ax.bar(x, f1_data['PLE-GRU'], width, label='PLE-GRU', color=colors['PLE-GRU'])
bars3 = ax.bar(x + width, f1_data['Hybrid Fusion'], width, label='Hybrid Fusion', color=colors['Hybrid Fusion'])

ax.set_xlabel('Training Data Percentage (%)', fontsize=12)
ax.set_ylabel('F1-Score (%)', fontsize=12)
ax.set_title('F1-Score Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{p}%' for p in training_percentages])
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3)

# Extract handles and labels to build a unified figure legend
handles, labels = ax.get_legend_handles_labels()

# Add a single shared legend at the bottom center of the figure
# ncol=3 spreads the elements horizontally
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=12)

# Adjust layout to prevent overlap, reserving the bottom 8% (rect parameter) for the legend space
plt.tight_layout(rect=[0, 0.08, 1, 1])

# Save the figure
output_dir = os.path.join(os.path.dirname(__file__), 'plots')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'model_performance_comparison.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✅ Charts saved to: {output_path}")

# Show the plot
plt.show()
