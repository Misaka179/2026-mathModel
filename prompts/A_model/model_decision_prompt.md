题目路径+调用更新后的math-modeling相关skill，并在原有的workflow基础下，根据以下要求完成建模手相关工作：

一、

推进建模手工作至G2.5阶段时（调用`problem-parser`、`problem-classifier`、`related-paper-analyzer` → `method-selector`、`decision-prompt-builder` → `modeler-decision-logger`），分析过程中同步回答以下问题 ，并写在题目分析报告.md的开头补充以下内容。

1. 用简洁语言概括这道题的核心研究对象；
2. 判断题目本质上属于哪一类问题，例如预测、评价、优化、调度、分类、规划、仿真或多目标决策；
3. 分析每个小问分别要解决什么问题；
4. 说明各小问之间是否存在递进关系；
5. 找出题目中的输入数据、输出结果、决策变量和约束条件；
6. 给出一个适合论文展开的整体主线；
7. 指出这道题最容易做错或写散的地方。
   要求：回答要面向数学建模竞赛论文写作，不要泛泛而谈，要尽量形成可执行的建模路线。

二、调用modeler-decision-logger冻结决策并形成记录前完成以下设置

1. G2阶段执行完related-paper-analyzer但调用method-selector前，暂存分析得出的2~4 候选模型和执行优先级相关数据，并对每个候选模型给出以下信息总结。

   | 项目       | 内容 |
   | ---------- | ---- |
   | 方案名称   |      |
   | 解决的问题 |      |
   | 核心思路   |      |
   | 决策变量   |      |
   | 数据处理   |      |
   | 核心模型   |      |
   | 关键公式   |      |
   | 约束       |      |
   | 求解方法   |      |
   | 评价指标   |      |
   | 优点       |      |
   | 缺点       |      |
   | 数据要求   |      |
   | 计算成本   |      |
   | 主要风险   |      |

2. 根据上一步的各候选方案信息，调用/chorus并使用"C:\Users\Song\.chorus\templates\q1-model-review.yaml"此模板完成所有候选方案评审。（评审时调取math-modeling建模手角色的相关skill，路径为C:\Users\Song\.claude\skills\math-modeling\references\roles\建模手）保存所有模型的评审资料，并以此为根据辅助随后调用method-selector所完成的最终选择。

3. 完成method-selector的调用后，对最终的选择模型保留其方案描述，并保留md文件为“暂定方案.md"。从此处开始，随后的agent工作不允许更换模型。随后以此为根据，调用/chorus且以"C:\Users\Song\.chorus\templates\mam-model-review.yaml"为模板进行三方审核并给出审核评价。（（评审时调取math-modeling建模手、代码手角色的相关skill，路径为C:\Users\Song\.claude\skills\math-modeling\references\roles）

4. 三方审查时，具体角色检查内容如下：

   * 数学建模审查员：

   变量；

   目标；

   约束；

   数学逻辑；

   假设；

   模型类型。

   * 数据审查员：

   数据是否支持；

   数据质量；

   参数来源；

   分布假设；

   数据泄漏；

   数据处理。

   * 算法审查员：

   LP/MILP/NLP；

   求解器；

   GA；

   收敛；

   复杂度；

   参数；

   可复现性。

5. G2.5阶段调用decision-prompt-builder时先启用学习模式。

   三、

   完成G2.5阶段建模手工作并选出最终模型后，回答以下问题并加入在题目分析报告.md的末尾

   1. 本问要解决的核心问题；
   2. 本问的输入数据；
   3. 本问的输出结果；
   4. 本问的决策变量；
   5. 本问的目标函数；
   6. 本问的关键约束条件；
   7. 每个约束的现实含义；
   8. 本问适合采用的求解方法；
   9. 本问结果应该如何验证；
   10. 本问应该生成哪些图表支撑论文分析。

   