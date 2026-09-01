# Troubleshooting

常见问题的排查指引。遇到不确定的情况先 STOP，再按这里排查；解决不了拉人。

## Git 冲突

- **原因**：多人改同一文件。按 `docs/handoff.md` 的目录权限表，原则上只改自己的目录。
- **处理**：交接前先 `git pull`；冲突时保留「负责人」版本的改动，另一人确认后合入。

## 结果异常 / 模型冲突

- 停止执行（Rule 9 / Rule 17），在群里同步现象与相关文件。
- 若涉及冻结模型：需要新建 `model_decision.md` 记录并重新冻结（Rule 15）。

## 论文数字找不到来源

- 核对 `05_results/verified_results.md`；若结果文件缺失或过期，返回 B 补齐，禁止编造。

## 路径 / 目录不一致

- skill 原生输出在个人本地 workspace（`planning/ methods/ code/ …`）；进仓库时按 `docs/workflow.md` 末尾的映射表归档到 `questions/Qx/` 编号目录。
- 找不到文件时先确认交接双方是否都 pull 到最新。

## skill 不生效

- 确认已运行 install 脚本并重启 Claude Code。
- 确认 skill 在 `~/.claude/skills/` 下。

## 环境问题

- MATLAB / 北太天元 缺失：确认实现语言选 Python，或装好 MATLAB 后再跑。
- Python 依赖缺失：`pip install numpy pandas matplotlib` 等按需安装。
