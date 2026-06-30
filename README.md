# Agent-Learning-Hub

**Stage1**：

![image-20260603222945743](README.assets/image-20260603222945743.png)

Hello Agent：![image-20260603223237205](README.assets/image-20260603223237205.png)

~~**优秀资源** 待完成内容学习后进行学习~~

完成了Hello-Agent第一章，初识智能体的阅读

---------

完成了Hello-Agent第二章—智能体发展史（系统再了解到了智能体）

​				第三章—大语言模型基础（算是把学过的机器学习和深度学习串着再复习了一遍）

----

完成Hello-Agent 第四章—智能体经典范式构建的学习

![image-20260605221226937](README.assets/image-20260605221226937.png)

系统性的通过编码回顾了这三种范式

---------

完成Hello-Agent 第五章—基于低代码平台的智能体搭建的学习

了解并实操了几个代表性的平台：Coze，Dify，FastGPT，n8n

---------

完成了Hello-Agent 第六章—框架开发实践

复习了LangGraph 以及了解到其他开发框架如：AutoGen、AgentScope、CAMEL

---------

完成了Hello-Agent 第七章—构建你的Agent框架

一步步构建了一个基础的智能体框架——HelloAgents。这个过程始终遵循着“分层解耦、职责单一、接口统一”的核心原则。

---------

完成了Hello-Agent 第八章—记忆与检索

为HelloAgents增加两个核心能力：**记忆系统（Memory System）**和**检索增强生成（Retrieval-Augmented Generation, RAG）**

---------

完成了Hello-Agent第九章—上下文工程

1. **ContextBuilder**：实现了 GSSC 流水线，提供统一的上下文管理接口
2. **NoteTool**：Markdown+YAML 的混合格式，支持结构化的长期记忆
3. **TerminalTool**：安全的命令行工具，支持即时的文件系统访问

级联效应：上游阶段的失效会被下游阶段放大。例如 Select 阶段混入大量无关信息，会导致 Compress 阶段无法精准识别核心内容，进一步加剧信息丢失或腐蚀。

---------

~~紧张刺激的期末周终于结束了~~

完成了Hello-Agent第十章—智能体通信协议 的学习

**协议定位：**

- **MCP (Model Context Protocol)**: 作为智能体与工具之间的桥梁，提供统一的工具访问接口，适用于增强单个智能体的能力。
- **A2A (Agent-to-Agent Protocol)**: 作为智能体之间的对话系统，支持直接通信与任务协商，适用于小规模团队的紧密协作。
- **ANP (Agent Network Protocol)**: 作为智能体的“互联网”，提供服务发现、路由与负载均衡机制，适用于构建大规模、开放的智能体网络。

- 优先利用成熟的社区 MCP 服务，以减少不必要的重复开发。
- 根据系统规模选择合适的协议：小规模协作场景推荐使用 A2A，大规模网络场景则应采用 ANP。

---------

完成Hello-Agent第十一章— Agent RL的学习

完整的 Agentic RL 训练流程包括:

1. **预训练(Pretraining)**:在大规模文本上学习语言知识(通常使用现成的预训练模型)
2. **监督微调(SFT)**:学习任务格式和基础推理能力
3. **强化学习(RL)**:通过试错优化推理策略，超越训练数据质量

其中，SFT 是基础，RL 是提升。没有 SFT 的基础，RL 很难成功;没有 RL 的优化，模型只能模仿训练数据。

(这一章内容比较难消化，等以后有时间再阅读相关资料深入理解一下)

完成Hello-Agent第十二章—智能体性能评估的学习

- 客观衡量智能体的能力
- 发现和修复问题
- 持续改进系统

---------



