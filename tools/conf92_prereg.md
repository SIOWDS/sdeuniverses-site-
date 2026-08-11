预注册 · 《步骤留下，岔路删除》实测
锁定时间：2026-08-11（在读取任何相关系数之前写定）
数据：O*NET 29.1 Work Context（Scale ID = CX），职业层，n≈870+

操作化（全部为 O*NET 原始描述符，不做任何合成加权）：
  A  自动化程度      4.C.3.b.2   Degree of Automation
  R1 例行度          4.C.3.b.7   Importance of Repeating Same Tasks
  R2 结构化程度      4.C.3.b.8   Structured versus Unstructured Work（反向计分后为结构化）
  W1 后果重量        4.C.3.a.2.a Impact of Decisions on Co-workers or Company Results
  W2 差错后果        4.C.3.a.1   Consequence of Error
  W3 人身安全责任    4.C.1.c.1   Responsible for Others' Health and Safety
  F  决策频次        4.C.3.a.2.b Frequency of Decision Making
  L  自由度          4.C.3.a.4   Freedom to Make Decisions
  T  时间压力        4.C.3.d.1   Time Pressure

预言（判定规则事先写死）：
  P1【靶心】删除顺序按可结算性而非后果重量：
     r(A,R) 显著为正，且 |r(A,R)| 明显大于 |r(A,W)|；
     控制 W 后 R 与 A 的偏相关仍显著为正；控制 R 后 W 与 A 的偏相关不显著。
     判否：若 |r(A,W)| ≥ |r(A,R)|，或控制 R 后 W 仍是 A 的强预测项，则 P1 伪。
  P2【两笔账】忙与选是两笔账：|r(T,L)| < 0.20，且 r(A,T) 不显著为负。
     判否：若 r(T,L) 强负（≤ -0.40），说明忙即无选择，本文的分账多余。
  P3【三条件不可归约】L（看得见/被允许）、R2 反向（路是否分开）、W1（后果落身）
     在主成分分析中不塌成一个维度：第一主成分解释方差 < 80%，且 W1 在第二主成分上有主要载荷。
     判否：第一主成分 ≥ 80% 且三者同号高载荷，则三条件是同一维度的三种说法，本文的三条件判据应被放弃。
  P4【频次不等于自由】r(F,L) 与 r(F,A) 方向相反，且 F 与 A 的负相关弱于 L 与 A 的负相关。
     判否：若 F 与 L 相关 ≥0.80，则"频次"与"自由"不可分，读数应合并。

不利结果一律照报，不做事后加权、不换指标、不删样本。
