# 证件照制作与交付检查

用途和官方造型／采集要求先读 `id-photo-official-requirements.md`，路由索引见 `../assets/id-photo-purpose-profiles.json`；规格解析使用 `id-photo-size-map.md`，通用头肩位置使用 `id-photo-composition.md`，用途专属几何优先。本页规定制作边界与导出验收。

## 用途是交付前提

记录具体用途、受理地区／机关、办理渠道、当前规则来源和核验日期，按用途检查首饰、头发与眉耳遮挡、衣领着装、妆容眼镜、表情、专属头部几何、处理许可及采集方式。只有尺寸或底色不能确定官方适用性，未知规则不得勾选通过。

规则禁止修改／合成或要求现场采集时，不通过数字去耳环、重画被遮住的耳朵、生成式扎发换装来替代本人重拍。以下非生成式处理也必须先获该用途渠道允许。虚构人物按明确授权制作的造型测试另见下文，不适用于真实官方交付。

## 先检查源图

检查正面、清晰度、完整头顶、颈部与必要肩部。全身照裁出的人脸可能像素不足；放大后模糊、重绘五官或生成新的面部细节不能算严格保真通过，应请求清晰近照。测试使用虚构人物时须与真实客户保真验收分开记录。

源图检查是制作前的停止门槛：先按目标取景查看原始像素的人脸、眼线、头顶、颈部和肩部；发现可见歪头、侧转、遮挡或细节不足时，不进入正式成片流程，不先生成一张“更像证件照”的新脸。不要仅以整张照片的分辨率判断脸部是否清晰，也不把人脸框或检测器返回的零角度当作正面姿态通过。无可靠检测器时直接视觉观察，不捏造自动识别结果。

测试人物也执行同一源图门槛。用户缺少素材时，可在已授权生成测试素材的范围内制作清晰正面头肩近照；已有确认参考但它不适合证件照时，先说明问题。重新生成的近照必须标为新的合成测试源并得到确认后才能作为基准，不能称为旧参考的原像素修复或真实客户保真测试。

证件照优先保留原面部、头发、表情与衣物，只调整已允许的背景、曝光、白平衡和整体裁切。不得让生成工具重绘面部后，仅因“看起来像”就宣称严格保真。缺失身体或原图姿态不合格时按构图规则停止，不通过补画或换脸修复。

严格保真走非生成式处理：用保留原始 RGB 的抠图遮罩更换背景，再按完整人物等比裁切、缩放及保守调色。不使用整图生成或生成式超分辨率重造五官；没有能保留主体像素的工具时报告处理能力不足。不得为通过构图数值局部修头、缩脸、拉颈或改肩。未经允许不换衣、不去配饰、不改变表情。

## 背景与画面

- 底色是独立规格。按已确认颜色处理，检查整片可见背景的均匀性、发丝与耳部边缘、颈肩过渡，不留光晕、残景、硬抠边或不需要的阴影。
- 与原参考并排看脸型、五官、发际线、年龄和配饰。两眼、鼻、口清楚，头部姿态自然，不能用美化改变身份。服装更换必须已明确要求，且不能覆盖严格用途的限制。
- 在最终导出文件上按构图表复核头顶、下巴、中心、侧边净空和双肩。导出前合格不代表中心裁切后仍合格；必要时调整完整裁切框，再导出。
- 人工测得的标记点可用于数值核对，但须说明是人工观察值；未检测到标记点时报告待人工检查，不伪造自动人脸识别通过。

## 文件导出

使用 `scripts/format_image.py` 生成独立文件，保留原图。先确定合格裁切，可用 `--crop-box LEFT TOP RIGHT BOTTOM` 指定原图坐标，再导出精确像素和指定 DPI、格式。坐标基于 EXIF 方向纠正后的原图，不能越界补画主体。该脚本只做等比缩放、裁切或补边；`--background` 用于补边或透明图层合成，**不会识别并替换不透明照片中的原背景**。

有文件体积上限时使用 `--max-bytes`，可配 `--min-quality` 控制 JPEG 最低质量。达到质量下限仍超限时应失败并报告，不悄悄缩小像素或输出模糊文件。PNG 等无损格式超限时同样停止，不擅自改格式。体积单位按机构定义换算；例如 100 KiB 是 102400 字节，不默认等于 100000 字节。

```bash
python scripts/format_image.py prepared.png final.jpg --width 413 --height 579 --dpi 300 --max-bytes 102400
python scripts/check_id_photo.py final.jpg --width 413 --height 579 --dpi 300 --format JPEG --max-bytes 102400
```

检查器验证可解码性、实际格式、像素、DPI、RGB、透明度和文件体积。可用 `--background '#FFFFFF'` 对上方两角做有限抽样；下方两角可能是肩膀或衣服，不作为背景判据。抽样不能证明全背景或抠图边缘合格，角落被头发占据时也需人工区分。`--landmarks observations.json` 只适用于 `generic_sample` 通用构图；官方用途的几何必须按当前规则独立测量并记录 `purpose_geometry`，检查器拒绝用通用标记点替代官方用途验收。

检查器没有人脸识别、分割和身份比对能力。文件检查通过后仍必须完成身份、源图清晰度、背景全域、轮廓和姿态的视觉检查。交付明确区分“文件参数通过”“视觉检查结果”和“机构接收结果”，不把前两者说成一定通过官方审核。

## 正式交付门槛

正式文件导出后，必须打开该最终文件，与原参考按等比例并排对照；不能把预处理图或旧版检查结果复用到新文件。逐项记录源图适用性、身份、原始细节、姿态、全背景与边缘、头肩构图、自然比例及用途专项。每项写具体观察，失败或待定均不能写 `pass`。检查器只验证记录完整性和文件哈希，不读取官方网页、检测耳环或判断规则来源是否适用，不代替视觉和用途判断，也不证明原像素保留或官方可接收。

将观察保存为 review JSON：

```json
{
  "source_sha256": "原参考文件的 SHA-256",
  "image_sha256": "最终独立文件的 SHA-256",
  "source_kind": "real_photo",
  "processing": "non_generative",
  "method": "assistant_visual",
  "reviewer": "实际检查者",
  "purpose_profile": "exam_registration",
  "requirements": {
    "verified": false,
    "scope": "实际地区、用途和渠道的适用范围，不能复制模板为已核实",
    "checked_on": "2026-10-22",
    "official_sources": [],
    "context": {"exam_name": "待核实", "year_or_session": "待核实", "region": "待核实", "submission_channel": "待核实"}
  },
  "checks": {
    "source_suitability": {"status": "pending", "note": "原图正面、头肩完整及适用性观察"},
    "identity": {"status": "pending", "note": "与原图的五官、脸型对照"},
    "source_detail": {"status": "pending", "note": "原始脸部细节及目标尺寸观察"},
    "pose": {"status": "pending", "note": "眼线、头部朝向及肩线观察"},
    "entire_background_and_edges": {"status": "pending", "note": "整片背景、发丝和颈肩边缘观察"},
    "head_and_shoulders": {"status": "pending", "note": "最终构图与头肩位置观察"},
    "natural_proportions": {"status": "pending", "note": "脸部、颈部及肩宽是否自然且未形变"},
    "hair_and_ears": {"status": "pending", "note": "依该用途检查眉眼、耳廓及头发遮挡"},
    "accessories": {"status": "pending", "note": "耳饰项链头饰的用途规则和可见结果"},
    "attire": {"status": "pending", "note": "衣服、领口与制服限制"},
    "makeup_and_eyes": {"status": "pending", "note": "妆容、眼镜、美瞳和反光规则"},
    "expression": {"status": "pending", "note": "中性表情、睁眼正视等用途规定"},
    "purpose_geometry": {"status": "pending", "note": "该用途的实际头宽头高顶距等测量及判据"},
    "processing_allowed": {"status": "pending", "note": "处理是否获接收渠道允许，不能默认保守处理均允许"},
    "submission_channel": {"status": "pending", "note": "是否需要现场采集、照片回执、近期本人或原始拍摄"}
  }
}
```

人工检查使用 `human_visual`，不得把助手判断写成人工批准。`processing` 区分 `unmodified_capture`、`non_generative` 和仅用于样张的 `generative_test`；即便未作生成式编辑，禁止编辑的纸质护照来源也不接受默认非生成式处理路径。SHA-256 用标准哈希库或系统工具对真实文件计算。完成真实用途核验后执行：

```bash
python scripts/check_id_photo.py final.jpg --width 413 --height 579 --dpi 300 --format JPEG --source original.png --review review.json --purpose exam_registration --require-review
```

命令中的用途、像素等均须按实际场景替换；review的 `purpose_profile` 必须与 `--purpose` 一致。缺用途或完整专项记录的旧版七项检查不能再放行。只有真实原始来源、用途规则及视觉全部通过，且 `file_checks_passed` 与 `delivery_ready` 为真，才可称该用途本地交付检查通过，仍不等于机构接受。任何源图或成片更换都会使旧哈希失效，需重新看图检查。机构审核结果保持 `not_evaluated`。

## 虚构人物造型样张

用户明确授权用已确认人物测试时，可生成整理头发、去饰、换深色衣服的整张造型预览，醒目标示“AI测试样张／非办证提交照片”；这不是对旧源图的原像素修复。可见造型合格不代表满足本人近期、原始采集或禁止合成条件，拼图也不代替独立文件精确尺寸验收。不要在用户确认前批量生成独立样张。

只有用户要求独立测试文件并完成相应文件检查时，使用 `source_kind: synthetic_test_source`、正确的处理类型及 `--test-sample`：

```bash
python scripts/check_id_photo.py sample.jpg --width 390 --height 567 --source approved-reference.png --review sample-review.json --purpose cn_passport_paper --test-sample --require-review
```

测试模式最多返回 `local_checks_passed: true` 和 `test_sample_ready: true`；`delivery_ready` 永远为假，不能用于声明官方合格。测试记录中的处理／采集项目说明“仅样张，真实提交不满足”，不能冒写该渠道允许AI合成。不提供 `--test-sample` 时，合成来源或生成式样张会阻止交付。

源图不合格时只说明原因；用户明确要求查看诊断效果时可展示保留原像素的诊断预览，必须醒目标明未通过，不称为正式成片，也不通过反复生成掩盖源图问题。
