# -*- coding: utf-8 -*-
"""Freeman et al. 2014 SI 文献表（refs 49-234）K/N 试编码。

唯一一条事先写死的编码问题：
  该干预的**定义**里，是否包含一条「学生交出之前教师不给出结论」的规则？
    K = 是（该规则是方法的构成要件）
    N = 否（只增加学生活动的频次或形式，未动谁在何时给出结论）
    ? = 仅凭方法名不可判定，须回原文方法部分

数据来源：SI 参考文献 49-234 的题名方法词（编号保留以便逐条回核）。
本脚本不含效应量与班额（Table S4 为 DOCX 附件，未取得），
因此这是一次**可行性试编码**，不是调节分析。
"""
import json
from collections import Counter
from pathlib import Path

R = [
 (49,"integrated curriculum / studio","?"),(50,"hot seat questioning","?"),
 (51,"SCALE-UP","?"),(52,"studio physics","?"),(53,"cooperative learning","?"),
 (54,"student-centered pedagogy","?"),(55,"reformed calculus","?"),
 (56,"cooperative learning","?"),(57,"APOS graphic understanding","?"),
 (58,"APOS cosets","?"),(59,"cooperative learning","?"),(60,"cooperative learning","?"),
 (61,"project LITE materials","N"),(62,"problem-based learning","K"),
 (63,"lecture-demonstration vs problem-solving","K"),(64,"conceptual change + group","?"),
 (65,"cooperative learning","?"),(66,"discussions in small groups","?"),
 (67,"problem-based learning","K"),(68,"physics learning","?"),
 (69,"lab based calculus","?"),(70,"interactive learning","?"),
 (71,"personalized instruction","N"),(72,"learning by writing","N"),
 (73,"organic course without a lecture","?"),(74,"student response system","N"),
 (75,"active and cooperative learning","?"),(76,"active learning","?"),
 (77,"hands-on VECTOR","?"),(78,"student-centered constructivist","?"),
 (79,"interactive engagement","?"),(80,"team-based learning","?"),
 (81,"case studies","?"),(82,"online homework system","N"),
 (83,"changed learning environment","?"),(84,"peer instruction","K"),
 (85,"writing summaries","N"),(86,"web lecture","N"),
 (87,"cooperative learning","?"),(88,"two instructional formats","?"),
 (89,"cooperative learning","?"),(90,"peer instruction","K"),
 (91,"cooperative learning","?"),(92,"cooperative learning","?"),
 (93,"modeling-based course","?"),(94,"Tablet PC interactivity","N"),
 (95,"multimedia","N"),(96,"course redesign","?"),
 (97,"engineering performance","?"),(98,"calculus reform","?"),
 (99,"statistical discovery materials","?"),(100,"personalized system of instruction","N"),
 (101,"cooperative learning","?"),(102,"active and cooperative learning","?"),
 (103,"unannounced quizzes","N"),(104,"cockpit physics curriculum","?"),
 (105,"context-based modular","?"),(106,"weekly quizzes","N"),
 (107,"cooperative learning","?"),(108,"interactive engagement","?"),
 (109,"research-based tutorials","K"),(110,"group learning + peer assessment","K"),
 (111,"studio style classrooms","?"),(112,"problem-based learning","K"),
 (113,"systematic instruction model","N"),(114,"curricular strategies","?"),
 (115,"cognitive apprenticeship","?"),(116,"cooperative learning","?"),
 (117,"response-card instruction","N"),(118,"analytical thinking methods","?"),
 (119,"constructing knowledge in lecture hall","?"),(120,"lecturing less","?"),
 (121,"retention","?"),(122,"tutorials / interactive tutorial lectures","K"),
 (123,"hybrid course","N"),(124,"programmed instruction","N"),
 (125,"peer instruction","K"),(126,"guiding questions with videos","N"),
 (127,"clicker methodology","N"),(128,"problem-based learning","K"),
 (129,"peer instruction","K"),(130,"peer-led guided inquiry","K"),
 (131,"two approaches to infinite series","?"),(132,"active learning in mechanics","?"),
 (133,"problem-based unit","K"),(134,"constructivist teaching","?"),
 (135,"constructivist teaching","?"),(136,"reading instruction","N"),
 (137,"cooperative learning","?"),(138,"higher level questions","?"),
 (139,"active techniques + lecture","?"),(140,"instructional design methods","?"),
 (141,"tutorials in introductory physics","K"),(142,"clickers","N"),
 (143,"how students think","?"),(144,"concept tests","?"),
 (145,"learner-centered course","?"),(146,"web-enhanced pedagogy","N"),
 (147,"hybrid lecture-online","N"),(148,"calculus & mathematica","?"),
 (149,"reform teaching methodology","?"),(150,"active learning variants","?"),
 (151,"studio format","?"),(152,"clickers","N"),
 (153,"problem-based learning","K"),(154,"misconceptions","?"),
 (155,"cloning the professor","?"),(156,"problem solving + cooperative","?"),
 (157,"cooperative learning","?"),(158,"active learning environment","?"),
 (159,"active learning curriculum","?"),(160,"collaborative learning","?"),
 (161,"adaptive expertise","?"),(162,"computer-based calculus","N"),
 (163,"wireless classroom communication","N"),(164,"individual response technology","N"),
 (165,"sustaining reforms","?"),(166,"interactive instruction","?"),
 (167,"cooperative learning","?"),(168,"cooperative learning","?"),
 (169,"microcomputer-based laboratories","?"),(170,"interaction vs lecture","?"),
 (171,"calculus and mathematica","N"),(172,"challenge-based instruction","K"),
 (173,"active learning strategies","?"),(174,"technology-enhanced instruction","N"),
 (175,"case-based approach","?"),(176,"cooperative learning","?"),
 (177,"cooperative learning laboratory","?"),(178,"POGIL","K"),
 (179,"New Studio format","?"),(180,"lecture quizzes","N"),
 (181,"interactive lecture demonstrations","N"),(182,"small-group peer teaching","K"),
 (183,"peer-led team learning","K"),(184,"active and collaborative learning","?"),
 (185,"workshop biology","?"),(186,"problem-based learning","K"),
 (187,"small group interaction","?"),(188,"interactive lectures","?"),
 (189,"constructive classroom activities","?"),(190,"case study physics","?"),
 (191,"active learning in large lecture","?"),(192,"active learning","?"),
 (193,"discovery learning","K"),(194,"group problem-solving","?"),
 (195,"active learning","?"),(196,"interactive lecture demonstrations","N"),
 (197,"integrated curricula","?"),(198,"learner-centered methods","?"),
 (199,"wireless laptops","N"),(200,"exam frequency","N"),
 (201,"peer-led team learning","K"),(202,"holistic teaching","?"),
 (203,"peer led team learning","K"),(204,"peer learning","K"),
 (205,"cooperative learning","?"),(206,"student profile data","?"),
 (207,"student response system","N"),(208,"social action project","?"),
 (209,"cooperative learning + peer instruction","K"),(210,"small-group instruction","?"),
 (211,"guided inquiry","K"),(212,"small group approach","?"),
 (213,"peer-led team learning","K"),(214,"active learning techniques","?"),
 (215,"student learning communities","?"),(216,"discipline-based intro course","?"),
 (217,"networked tools","N"),(218,"cooperative learning","?"),
 (219,"revisiting mathematics","?"),(220,"need-based learning","?"),
 (221,"team-based learning","?"),(222,"optimizing student success","?"),
 (223,"small groups","?"),(224,"Just-in-Time Teaching","?"),
 (225,"active learning strategies","?"),(226,"calculus reform","?"),
 (227,"active learning tools","?"),(228,"PBL seven steps","K"),
 (229,"active and cooperative learning","?"),(230,"audience paced feedback","N"),
 (231,"peer-led workshops","K"),(232,"peer-led team learning","K"),
 (233,"daily class progress assessment","N"),(234,"PER-based reform","?"),
]

cnt = Counter(c for _, _, c in R)
tot = len(R)
print(f"条目 {tot} 条（SI 参考文献 49-234）\n")
for k, name in (("K","含推迟结论的规则"),("N","只增加活动量"),("?","方法名不足以判定")):
    print(f"  {k}  {name:<14} {cnt[k]:3d} 条  {cnt[k]/tot*100:4.1f}%")
print(f"\n可从方法名判定：{cnt['K']+cnt['N']} / {tot} = {(cnt['K']+cnt['N'])/tot*100:.1f}%")
print(f"必须回原文方法部分：{cnt['?']} / {tot} = {cnt['?']/tot*100:.1f}%")
print("\nK 集中在四族：同伴教学 / 同伴引导小组 / 引导式探究与 POGIL / 问题导向与教学导引")
print("N 集中在三族：应答器与测验 / 技术增量 / 演示与讲授节奏调整")
Path("/home/claude/pilot_coding.json").write_text(
    json.dumps([{"ref": n, "method": m, "code": c} for n, m, c in R],
               ensure_ascii=False, indent=1), encoding="utf-8")
print("\n编码表已存 pilot_coding.json（含编号，可逐条回核 SI）")
