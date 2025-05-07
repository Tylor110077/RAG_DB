import matplotlib.pyplot as plt
import numpy as np

# 数据
models = ['Benchmark models']
response_score = [5]
availability_score = [1]
accuracy_score = [1]
overall_score = [7]

# 设置参数
bar_width = 0.2
index = np.arange(len(models))

# 绘制柱状图
fig, ax = plt.subplots(figsize=(10, 6))

bar1 = ax.bar(index - 1.5 * bar_width, response_score, bar_width, label='Response')
bar2 = ax.bar(index - 0.5 * bar_width, availability_score, bar_width, label='Availability')
bar3 = ax.bar(index + 0.5 * bar_width, accuracy_score, bar_width, label='Accuracy')
bar4 = ax.bar(index + 1.5 * bar_width, overall_score, bar_width, label='Overall')

# 在柱子上显示数值
for bars in [bar1, bar2, bar3, bar4]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

# 设置标签和标题
ax.set_xlabel('Models')
ax.set_ylabel('Score')
ax.set_title('Performance Comparison Across Different Models')
ax.set_xticks(index)
ax.set_xticklabels(models)
ax.legend()

# 调整布局
plt.tight_layout()
plt.show()
